"""Nornir job for generating the intended config."""
# pylint: disable=relative-beyond-top-level
import logging
import os
from datetime import datetime

from django.utils.timezone import make_aware

from nautobot_plugin_nornir.constants import NORNIR_SETTINGS
from nautobot_plugin_nornir.plugins.inventory.nautobot_orm import NautobotORMInventory

from nornir import InitNornir
from nornir.core.plugins.inventory import InventoryPluginRegister
from nornir.core.task import Result, Task
from nornir_nautobot.exceptions import NornirNautobotException
from nornir_nautobot.plugins.tasks.dispatcher import dispatcher

from nautobot_golden_config.models import GoldenConfig

from nautobot_golden_config.nornir_plays.processor import ProcessGoldenConfig
from nautobot_golden_config.utilities.db_management import close_threaded_db_connections

from nautobot_golden_config.utilities.graphql import graph_ql_query
from nautobot_golden_config.utilities.helper import (
    dispatch_params,
    get_django_env,
    get_device_to_settings_map,
    get_job_filter,
    render_jinja_template,
    verify_settings,
)
from nautobot_golden_config.utilities.logger import NornirLogger

InventoryPluginRegister.register("nautobot-inventory", NautobotORMInventory)
LOGGER = logging.getLogger(__name__)


@close_threaded_db_connections
def run_template(  # pylint: disable=too-many-arguments,too-many-locals
    task: Task, logger: NornirLogger, device_to_settings_map, job_class_instance, jinja_env
) -> Result:
    """Render Jinja Template.

    Only one template is supported, so the expectation is that that template includes all other templates.

    Args:
        task (Task): Nornir task individual object
        logger (NornirLogger): Logger to log messages to.
        global_settings (GoldenConfigSetting): The settings for GoldenConfigPlugin.
        job_class_instance (Result): The the output from the Nautobot Job instance being run.

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
    job_class_instance.request.user = job_class_instance.user
    status, device_data = graph_ql_query(job_class_instance.request, obj, settings.sot_agg_query.query)
    if status != 200:
        error_msg = f"`E3012:` The GraphQL query return a status of {str(status)} with error of {str(device_data)}"
        logger.error(error_msg, extra={"object": obj})
        raise NornirNautobotException(error_msg)

    task.host.data.update(device_data)

    generated_config = task.run(
        task=dispatcher,
        name="GENERATE CONFIG",
        obj=obj,
        logger=logger,
        jinja_template=jinja_template,
        jinja_root_path=settings.jinja_repository.filesystem_path,
        output_file_location=output_file_location,
        jinja_filters=jinja_env.filters,
        jinja_env=jinja_env,
        **dispatch_params("generate_config", obj.platform.network_driver, logger),
    )[1].result["config"]
    intended_obj.intended_last_success_date = task.host.defaults.data["now"]
    intended_obj.intended_config = generated_config
    intended_obj.save()

    logger.info("Successfully generated the intended configuration.", extra={"object": obj})

    return Result(host=task.host, result=generated_config)


def config_intended(job_result, log_level, data, job_class_instance):
    """
    Nornir play to generate configurations.

    Args:
        logger (NornirLogger): The Nautobot Job instance being run.
        job_class_instance (Job): The Nautobot Job instance being run.
        data (dict): Form data from Nautobot Job.

    Returns:
        None: Intended configuration files are written to filesystem.
    """
    now = make_aware(datetime.now())
    logger = NornirLogger(job_result, log_level)

    try:
        qs = get_job_filter(data)
    except NornirNautobotException as error:
        error_msg = f"`E3008:` General Exception handler, original error message ```{error}```"
        logger.error(error_msg)
        raise NornirNautobotException(error_msg) from error

    logger.debug("Compiling device data for intended configuration.")
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

            logger.debug("Run nornir render config tasks.")
            # Run the Nornir Tasks
            nr_with_processors.run(
                task=run_template,
                name="RENDER CONFIG",
                logger=logger,
                device_to_settings_map=device_to_settings_map,
                job_class_instance=job_class_instance,
                jinja_env=jinja_env,
            )

    except Exception as error:
        error_msg = f"`E3001:` General Exception handler, original error message ```{error}```"
        logger.error(error_msg)
        raise NornirNautobotException(error_msg) from error
