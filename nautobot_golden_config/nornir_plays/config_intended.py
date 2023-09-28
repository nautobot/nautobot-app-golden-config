"""Nornir job for generating the intended config."""
# pylint: disable=relative-beyond-top-level
import logging
import os
from datetime import datetime

from nautobot_plugin_nornir.constants import NORNIR_SETTINGS
from nautobot_plugin_nornir.plugins.inventory.nautobot_orm import NautobotORMInventory
from nautobot_plugin_nornir.utils import get_dispatcher
from nornir import InitNornir
from nornir.core.plugins.inventory import InventoryPluginRegister
from nornir.core.task import Result, Task
from nornir_nautobot.exceptions import NornirNautobotException
from nornir_nautobot.plugins.tasks.dispatcher import dispatcher
from nornir_nautobot.utils.logger import NornirLogger

from nautobot_golden_config.models import GoldenConfig
from nautobot_golden_config.nornir_plays.processor import ProcessGoldenConfig
from nautobot_golden_config.utilities.db_management import close_threaded_db_connections
from nautobot_golden_config.utilities.graphql import graph_ql_query
from nautobot_golden_config.utilities.helper import (
    get_django_env,
    get_device_to_settings_map,
    get_job_filter,
    render_jinja_template,
    verify_settings,
)

InventoryPluginRegister.register("nautobot-inventory", NautobotORMInventory)
LOGGER = logging.getLogger(__name__)


@close_threaded_db_connections
def run_template(  # pylint: disable=too-many-arguments
    task: Task, logger, device_to_settings_map, nautobot_job, jinja_env
) -> Result:
    """Render Jinja Template.

    Only one template is supported, so the expectation is that that template includes all other templates.

    Args:
        task (Task): Nornir task individual object
        logger (NornirLogger): Logger to log messages to.
        global_settings (GoldenConfigSetting): The settings for GoldenConfigPlugin.
        nautobot_job (Result): The the output from the Nautobot Job instance being run.

    Returns:
        result (Result): Result from Nornir task
    """
    obj = task.host.data["obj"]
    settings = device_to_settings_map[obj.id]

    intended_obj = GoldenConfig.objects.filter(device=obj).first()
    if not intended_obj:
        intended_obj = GoldenConfig.objects.create(device=obj)
    intended_obj.intended_last_attempt_date = task.host.defaults.data["now"]
    intended_obj.save()

    intended_directory = settings.intended_repository.filesystem_path
    intended_path_template_obj = render_jinja_template(obj, logger, settings.intended_path_template)
    output_file_location = os.path.join(intended_directory, intended_path_template_obj)

    jinja_template = render_jinja_template(obj, logger, settings.jinja_path_template)
    status, device_data = graph_ql_query(nautobot_job.request, obj, settings.sot_agg_query.query)
    if status != 200:
        logger.log_failure(obj, f"The GraphQL query return a status of {str(status)} with error of {str(device_data)}")
        raise NornirNautobotException(
            f"The GraphQL query return a status of {str(status)} with error of {str(device_data)}"
        )
    task.host.data.update(device_data)

    generated_config = task.run(
        task=dispatcher,
        name="GENERATE CONFIG",
        method="generate_config",
        obj=obj,
        logger=logger,
        jinja_template=jinja_template,
        jinja_root_path=settings.jinja_repository.filesystem_path,
        output_file_location=output_file_location,
        default_drivers_mapping=get_dispatcher(),
        jinja_filters=jinja_env.filters,
        jinja_env=jinja_env,
    )[1].result["config"]
    intended_obj.intended_last_success_date = task.host.defaults.data["now"]
    intended_obj.intended_config = generated_config
    intended_obj.save()

    logger.log_success(obj, "Successfully generated the intended configuration.")

    return Result(host=task.host, result=generated_config)


def config_intended(nautobot_job, data):
    """
    Nornir play to generate configurations.

    Args:
        nautobot_job (Result): The Nautobot Job instance being run.
        data (dict): Form data from Nautobot Job.

    Returns:
        None: Intended configuration files are written to filesystem.
    """
    now = datetime.now()
    logger = NornirLogger(__name__, nautobot_job, data.get("debug"))

    qs = get_job_filter(data)
    logger.log_debug("Compiling device data for intended configuration.")
    device_to_settings_map = get_device_to_settings_map(queryset=qs)

    for settings in set(device_to_settings_map.values()):
        verify_settings(logger, settings, ["jinja_path_template", "intended_path_template", "sot_agg_query"])

    # Retrieve filters from the Django jinja template engine
    jinja_env = get_django_env()

    try:
        with InitNornir(
            runner=NORNIR_SETTINGS.get("runner"),
            logging={"enabled": False},
            inventory={
                "plugin": "nautobot-inventory",
                "options": {
                    "credentials_class": NORNIR_SETTINGS.get("credentials"),
                    "params": NORNIR_SETTINGS.get("inventory_params"),
                    "queryset": qs,
                    "defaults": {"now": now},
                },
            },
        ) as nornir_obj:
            nr_with_processors = nornir_obj.with_processors([ProcessGoldenConfig(logger)])

            logger.log_debug("Run nornir render config tasks.")
            # Run the Nornir Tasks
            nr_with_processors.run(
                task=run_template,
                name="RENDER CONFIG",
                logger=logger,
                device_to_settings_map=device_to_settings_map,
                nautobot_job=nautobot_job,
                jinja_env=jinja_env,
            )

    except Exception as err:
        logger.log_failure(None, err)
        raise
