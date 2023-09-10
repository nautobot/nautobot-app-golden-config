"""Nornir job for deploying configurations."""
from datetime import datetime

from nornir import InitNornir
from nornir.core.task import Result, Task
from nornir.core.plugins.inventory import InventoryPluginRegister

from nornir_nautobot.exceptions import NornirNautobotException
from nornir_nautobot.plugins.tasks.dispatcher import dispatcher
from nornir_nautobot.utils.logger import NornirLogger

from nautobot.dcim.models import Device

from nautobot_plugin_nornir.plugins.inventory.nautobot_orm import NautobotORMInventory
from nautobot_plugin_nornir.constants import NORNIR_SETTINGS

from nautobot_golden_config.nornir_plays.processor import ProcessGoldenConfig

InventoryPluginRegister.register("nautobot-inventory", NautobotORMInventory)


def run_deployment(task: Task, logger: NornirLogger, commit: bool, config_plan_qs) -> Result:
    """Deploy configurations to device."""
    obj = task.host.data["obj"]
    plans_to_deploy = config_plan_qs.filter(device=obj)
    consolidated_config_set = "\n".join(plans_to_deploy.values_list("config_set", flat=True))
    logger.log_debug(f"Consolidated config set: {consolidated_config_set}")
    # TODO: Future: We should add post-processing rendering here
    # after https://github.com/nautobot/nautobot-plugin-golden-config/issues/443

    if commit:
        result = task.run(
            task=dispatcher,
            method="merge_config",
            obj=obj,
            logger=logger,
            custom_dispatcher={},
            name="DEPLOY CONFIG TO DEVICE",
            config=consolidated_config_set,
        )[1].result["result"]
        logger.log_info(obj=obj, message="Successfully deployed configuration to device.")
    else:
        result = None
        logger.log_info(obj=obj, message="Commit not enabled. Configuration not deployed to device.")

    return Result(host=task.host, result=result)


def config_deployment(job_result, data, commit):
    """Nornir play to deploy configurations."""
    now = datetime.now()
    logger = NornirLogger(__name__, job_result, data.get("debug"))
    logger.log_debug("Starting config deployment")

    config_plan_qs = data["config_plan"]
    if config_plan_qs.filter(status__slug="not-approved").exists():
        error_msg = "E3010: Cannot deploy configuration(s). One or more config plans are not approved."
        logger.log_error(error_msg)
        raise NornirNautobotException(error_msg)

    device_qs = Device.objects.filter(config_plan__in=config_plan_qs).distinct()

    try:
        with InitNornir(
            runner=NORNIR_SETTINGS.get("runner"),
            logging={"enabled": False},
            inventory={
                "plugin": "nautobot-inventory",
                "options": {
                    "credentials_class": NORNIR_SETTINGS.get("credentials"),
                    "params": NORNIR_SETTINGS.get("inventory_params"),
                    "queryset": device_qs,
                    "defaults": {"now": now},
                },
            },
        ) as nornir_obj:
            nr_with_processors = nornir_obj.with_processors([ProcessGoldenConfig(logger)])

            nr_with_processors.run(
                task=run_deployment,
                name="DEPLOY CONFIG",
                logger=logger,
                commit=commit,
                config_plan_qs=config_plan_qs,
            )
    except Exception as err:
        error_msg = f"E3011: {err}"
        logger.log_error(error_msg)
        raise NornirNautobotException(error_msg)

    logger.log_debug("Completed configuration deployment.")
