"""Nornir job for deploying configurations."""

import logging
from datetime import datetime

from django.contrib.auth import get_user_model
from django.utils.timezone import make_aware
from nautobot.dcim.models import Device
from nautobot.extras.models import Status
from nautobot_plugin_nornir.constants import NORNIR_SETTINGS
from nautobot_plugin_nornir.plugins.inventory.nautobot_orm import NautobotORMInventory
from nornir import InitNornir
from nornir.core.exceptions import NornirSubTaskError
from nornir.core.plugins.inventory import InventoryPluginRegister
from nornir.core.task import Result, Task
from nornir_nautobot.exceptions import NornirNautobotException
from nornir_nautobot.plugins.tasks.dispatcher import dispatcher

from nautobot_golden_config.nornir_plays.processor import ProcessGoldenConfig
from nautobot_golden_config.utilities.config_postprocessing import get_config_postprocessing
from nautobot_golden_config.utilities.constant import DEFAULT_DEPLOY_STATUS
from nautobot_golden_config.utilities.db_management import close_threaded_db_connections
from nautobot_golden_config.utilities.helper import dispatch_params
from nautobot_golden_config.utilities.logger import NornirLogger

InventoryPluginRegister.register("nautobot-inventory", NautobotORMInventory)


@close_threaded_db_connections
def run_deployment(task: Task, logger: logging.Logger, config_plan_qs, deploy_job_result, job_request) -> Result:
    """Deploy configurations to device."""
    obj = task.host.data["obj"]
    plans_to_deploy = config_plan_qs.filter(device=obj)
    plans_to_deploy.update(deploy_result=deploy_job_result)
    consolidated_config_set = "\n".join(plans_to_deploy.values_list("config_set", flat=True))
    logger.debug(f"Consolidated config set: {consolidated_config_set}")
    logger.debug("Executing post-processing on the config set")
    post_config = get_config_postprocessing(plans_to_deploy, job_request)
    plans_to_deploy.update(status=Status.objects.get(name="In Progress"))
    try:
        result = task.run(
            task=dispatcher,
            name="DEPLOY CONFIG TO DEVICE",
            obj=obj,
            logger=logger,
            config=post_config,
            can_diff=False,
            **dispatch_params("merge_config", obj.platform.network_driver, logger),
        )[1]
        task_changed, task_result, task_failed = result.changed, result.result, result.failed
        if task_changed and task_failed:
            # means config_revert happened in `napalm_configure`
            plans_to_deploy.update(status=Status.objects.get(name="Failed"))
            error_msg = "`E3023:` Failed deployment to the device."
            logger.error(error_msg, extra={"object": obj})
            raise NornirNautobotException(error_msg)

        if not task_changed and not task_failed:
            plans_to_deploy.update(status=Status.objects.get(name="Completed"))
            logger.info("Nothing was deployed to the device.", extra={"object": obj})
        elif not task_failed:
            logger.info("Successfully deployed configuration to device.", extra={"object": obj})
            plans_to_deploy.update(status=Status.objects.get(name="Completed"))
    except NornirSubTaskError as error:
        task_result = None
        plans_to_deploy.update(status=Status.objects.get(name="Failed"))
        error_msg = f"`E3024:` Failed deployment to the device with error: {error}"
        logger.error(error_msg, extra={"object": obj})
        raise NornirNautobotException(error_msg) from error

    return Result(host=task.host, result=task_result)


def config_deployment(job):
    """
    Nornir play to deploy configurations.

    Args:
        job (Job): The Nautobot Job instance being run.

    Returns:
        None: Deployment results are written to database.
    """
    now = make_aware(datetime.now())
    logger = NornirLogger(job.job_result, job.logger.getEffectiveLevel())

    logger.debug("Starting config deployment")
    config_plan_qs = job.data["config_plan"]
    if config_plan_qs.filter(status__name=DEFAULT_DEPLOY_STATUS).exists():
        error_msg = "`E3025:` Cannot deploy configuration(s). One or more config plans are not approved."
        logger.error(error_msg)
        raise NornirNautobotException(error_msg)
    if config_plan_qs.filter(status__name="Completed").exists():
        error_msg = "`E3026:` Cannot deploy configuration(s). One or more config plans are already completed."
        logger.error(error_msg)
        raise NornirNautobotException(error_msg)
    device_qs = Device.objects.filter(config_plan__in=config_plan_qs).distinct()
    User = get_user_model()  # pylint: disable=invalid-name
    job.request.user = User.objects.get(id=job.celery_kwargs["nautobot_job_user_id"])
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
                config_plan_qs=config_plan_qs,
                deploy_job_result=job.job_result,
                job_request=job.request,
            )
    except Exception as error:
        error_msg = f"`E3001:` General Exception handler, original error message ```{error}```"
        logger.error(error_msg)
        raise NornirNautobotException(error_msg) from error

    logger.debug("Completed configuration deployment.")
