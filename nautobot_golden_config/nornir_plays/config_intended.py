"""Nornir job for generating the intended config."""
# pylint: disable=relative-beyond-top-level
import os
import logging

from datetime import datetime
from nornir import InitNornir
from nornir.core.plugins.inventory import InventoryPluginRegister
from nornir.core.task import Result, Task

from django_jinja.backend import Jinja2

from nornir_nautobot.exceptions import NornirNautobotException
from nornir_nautobot.plugins.tasks.dispatcher import dispatcher
from nornir_nautobot.utils.logger import NornirLogger

from nautobot_plugin_nornir.plugins.inventory.nautobot_orm import NautobotORMInventory
from nautobot_plugin_nornir.constants import NORNIR_SETTINGS
from nautobot_plugin_nornir.utils import get_dispatcher

from nautobot_golden_config.models import GoldenConfigSetting, GoldenConfig
from nautobot_golden_config.utilities.helper import (
    get_job_filter,
    get_repository_working_dir,
    verify_global_settings,
    render_jinja_template,
)
from nautobot_golden_config.utilities.graphql import graph_ql_query
from nautobot_golden_config.nornir_plays.processor import ProcessGoldenConfig

InventoryPluginRegister.register("nautobot-inventory", NautobotORMInventory)
LOGGER = logging.getLogger(__name__)

jinja_settings = Jinja2.get_default()
jinja_env = jinja_settings.env


def run_template(  # pylint: disable=too-many-arguments
    task: Task, logger, global_settings, nautobot_job, jinja_root_path
) -> Result:
    """Render Jinja Template.

    Only one template is supported, so the expectation is that that template includes all other templates.

    Args:
        task (Task): Nornir task individual object
        logger (NornirLogger): Logger to log messages to.
        global_settings (GoldenConfigSetting): The settings for GoldenConfigPlugin.
        nautobot_job (Result): The the output from the Nautobot Job instance being run.
        jinja_root_path (str): The root path to the Jinja2 intended config file.

    Returns:
        result (Result): Result from Nornir task
    """
    obj = task.host.data["obj"]

    intended_obj = GoldenConfig.objects.filter(device=obj).first()
    if not intended_obj:
        intended_obj = GoldenConfig.objects.create(device=obj)
    intended_obj.intended_last_attempt_date = task.host.defaults.data["now"]
    intended_obj.save()

    intended_directory = get_repository_working_dir("intended", obj, logger, global_settings)
    intended_path_template_obj = render_jinja_template(obj, logger, global_settings.intended_path_template)
    output_file_location = os.path.join(intended_directory, intended_path_template_obj)

    jinja_template = render_jinja_template(obj, logger, global_settings.jinja_path_template)
    status, device_data = graph_ql_query(nautobot_job.request, obj, global_settings.sot_agg_query)
    if status != 200:
        logger.log_failure(obj, f"The GraphQL query return a status of {str(status)} with error of {str(device_data)}")
        raise NornirNautobotException()
    task.host.data.update(device_data)

    generated_config = task.run(
        task=dispatcher,
        name="GENERATE CONFIG",
        method="generate_config",
        obj=obj,
        logger=logger,
        jinja_template=jinja_template,
        jinja_root_path=jinja_root_path,
        output_file_location=output_file_location,
        default_drivers_mapping=get_dispatcher(),
        jinja_filters=jinja_env.filters,
    )[1].result["config"]
    intended_obj.intended_last_success_date = task.host.defaults.data["now"]
    intended_obj.intended_config = generated_config
    intended_obj.save()

    logger.log_success(obj, "Successfully generated the intended configuration.")

    return Result(host=task.host, result=generated_config)


def config_intended(nautobot_job, data, jinja_root_path):
    """
    Nornir play to generate configurations.

    Args:
        nautobot_job (Result): The Nautobot Job instance being run.
        data (dict): Form data from Nautobot Job.
        jinja_root_path (str): The root path to the Jinja2 intended config file.

    Returns:
        None: Intended configuration files are written to filesystem.
    """
    now = datetime.now()
    logger = NornirLogger(__name__, nautobot_job, data.get("debug"))
    global_settings = GoldenConfigSetting.objects.first()
    verify_global_settings(logger, global_settings, ["jinja_path_template", "intended_path_template", "sot_agg_query"])
    try:
        with InitNornir(
            runner=NORNIR_SETTINGS.get("runner"),
            logging={"enabled": False},
            inventory={
                "plugin": "nautobot-inventory",
                "options": {
                    "credentials_class": NORNIR_SETTINGS.get("credentials"),
                    "params": NORNIR_SETTINGS.get("inventory_params"),
                    "queryset": get_job_filter(data),
                    "defaults": {"now": now},
                },
            },
        ) as nornir_obj:

            nr_with_processors = nornir_obj.with_processors([ProcessGoldenConfig(logger)])

            # Run the Nornir Tasks
            nr_with_processors.run(
                task=run_template,
                name="RENDER CONFIG",
                logger=logger,
                global_settings=global_settings,
                nautobot_job=nautobot_job,
                jinja_root_path=jinja_root_path,
            )

    except Exception as err:
        logger.log_failure(None, err)
        raise
