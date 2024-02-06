"""Nornir job for deploying configurations."""

from datetime import datetime

from nautobot.dcim.models import Device
from nautobot.extras.models import Status
from nautobot_plugin_nornir.constants import NORNIR_SETTINGS
from nautobot_plugin_nornir.plugins.inventory.nautobot_orm import NautobotORMInventory
from nautobot_plugin_nornir.utils import get_dispatcher
from nornir import InitNornir
from nornir.core.exceptions import NornirSubTaskError
from nornir.core.plugins.inventory import InventoryPluginRegister
from nornir.core.task import Result, Task
from nornir_nautobot.plugins.tasks.dispatcher import dispatcher
from nornir_nautobot.utils.logger import NornirLogger

from nautobot_golden_config.utilities.db_management import close_threaded_db_connections
from nautobot_golden_config.nornir_plays.processor import ProcessGoldenConfig

InventoryPluginRegister.register("nautobot-inventory", NautobotORMInventory)


@close_threaded_db_connections
def run_deployment(task: Task, logger: NornirLogger, commit: bool, config_plan_qs, deploy_job_result) -> Result:
    """Deploy configurations to device."""
    obj = task.host.data["obj"]
    plans_to_deploy = config_plan_qs.filter(device=obj)
    plans_to_deploy.update(deploy_result=deploy_job_result.job_result)
    consolidated_config_set = "\n".join(plans_to_deploy.values_list("config_set", flat=True))
    logger.log_debug(f"Consolidated config set: {consolidated_config_set}")
    # TODO: We should add post-processing rendering here
    # after https://github.com/nautobot/nautobot-plugin-golden-config/issues/443

    if commit:
        plans_to_deploy.update(status=Status.objects.get(slug="in-progress"))
        try:
            result = task.run(
                task=dispatcher,
                name="DEPLOY CONFIG TO DEVICE",
                method="merge_config",
                obj=obj,
                logger=logger,
                config=consolidated_config_set,
                default_drivers_mapping=get_dispatcher(),
            )[1]
            task_changed, task_result, task_failed = result.changed, result.result, result.failed
            if task_changed and task_failed:
                # means config_revert happened in `napalm_configure`
                plans_to_deploy.update(status=Status.objects.get(slug="failed"))
                logger.log_failure(obj=obj, message="Failed deployment to the device.")
            elif not task_changed and not task_failed:
                plans_to_deploy.update(status=Status.objects.get(slug="completed"))
                logger.log_success(obj=obj, message="Nothing was deployed to the device.")
            else:
                if not task_failed:
                    logger.log_success(obj=obj, message="Successfully deployed configuration to device.")
                    plans_to_deploy.update(status=Status.objects.get(slug="completed"))
        except NornirSubTaskError:
            task_result = None
            plans_to_deploy.update(status=Status.objects.get(slug="failed"))
            logger.log_failure(obj=obj, message="Failed deployment to the device.")
    else:
        task_result = None
        logger.log_info(obj=obj, message="Commit not enabled. Configuration not deployed to device.")

    return Result(host=task.host, result=task_result)


def config_deployment(job_result, data, commit):
    """Nornir play to deploy configurations."""
    now = datetime.now()
    logger = NornirLogger(__name__, job_result, data.get("debug"))
    logger.log_debug("Starting config deployment")
    config_plan_qs = data["config_plan"]
    if config_plan_qs.filter(status__slug="not-approved").exists():
        message = "Cannot deploy configuration(s). One or more config plans are not approved."
        logger.log_failure(obj=None, message=message)
        raise ValueError(message)
    if config_plan_qs.filter(status__slug="completed").exists():
        message = "Cannot deploy configuration(s). One or more config plans are already completed."
        logger.log_failure(obj=None, message=message)
        raise ValueError(message)
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
                deploy_job_result=job_result,
            )
    except Exception as err:
        logger.log_failure(obj=None, message=f"Failed to initialize Nornir: {err}")
        raise

    logger.log_debug("Completed configuration deployment.")
