"""Nornir job for provisioning a candidate config."""
from datetime import datetime
from typing import Dict

from netutils.config.compliance import diff_network_config
from netutils.config.clean import clean_config

from nautobot.extras.jobs import Job
from nautobot_plugin_nornir.constants import NORNIR_SETTINGS
from nautobot_plugin_nornir.utils import get_dispatcher
from nornir import InitNornir
from nornir.core.task import Result, Task
from nornir.core.exceptions import NornirSubTaskError
from nornir_nautobot.exceptions import NornirNautobotException
from nornir_nautobot.plugins.tasks.dispatcher import dispatcher
from nornir_nautobot.utils.logger import NornirLogger

from nautobot_golden_config.models import ConfigRemove
from nautobot_golden_config.nornir_plays.processor import ProcessGoldenConfig
from nautobot_golden_config.utilities.helper import get_job_filter
from nautobot_golden_config.utilities.config_postprocessing import get_config_postprocessing


def run_provisioning(
    task: Task, logger: NornirLogger, http_request, dry_run: bool, remove_regex_dict: Dict, nautobot_job
) -> Result:
    r"""Checks for connectivity and runs the configuration provisioning task.

    Args:
        task (Task): Nornir task.
        logger (NornirLogger): Nornir logger.
        dry_run (bool): Dry run option that gives a diff between backup and candidate config.
        remove_regex_dict (dict): Dictionary used to remove lines in configuration with secrets, ex. {'cisco_ios': [{'regex': '^enable secret.*\\n'}, {'regex': 'sent-username.*\\n'}, {'regex': '^username.*\\n'}]}

    Returns:
        Result: Outcome of config provisioning task.
    """
    obj = task.host.data["obj"]
    test_connectivity = True  # to parametrize

    if test_connectivity is not False:
        task.run(
            task=dispatcher,
            name="TEST CONNECTIVITY",
            method="check_connectivity",
            obj=obj,
            logger=logger,
            default_drivers_mapping=get_dispatcher(),
        )

    # Get configuration per device
    # TODO: fix this, check that obj is device and nautobot_job has the request
    config = get_config_postprocessing(obj.configs, nautobot_job.request)

    if dry_run:
        try:
            running_config = task.run(
                task=dispatcher,
                name="SAVE RUNNING CONFIGURATION TO FILE",
                method="get_config",
                obj=obj,
                logger=logger,
                backup_file="",
                remove_lines="",
                substitute_lines="",
                default_drivers_mapping=get_dispatcher(),
            )[1].result["config"]
        except NornirSubTaskError as exc:
            logger.log_failure(obj, f"Connection error. `{exc.result.exception}`")
            raise NornirNautobotException()

        clean_filters = remove_regex_dict[obj.platform.slug]
        config_wo_secrets = clean_config(config, clean_filters)
        # diff configs using a simple diff that shows extra lines in config
        diff = diff_network_config(config_wo_secrets, running_config, obj.platform.slug).splitlines()

        logger.log_success(obj, f"Diff between candidate and backup configuration {diff}.")
        result = None

    else:
        result = task.run(
            task=dispatcher,
            name="PROVISION CONFIGURATION TO DEVICE",
            method="provision_config",
            obj=obj,
            logger=logger,
            config=config,
            default_drivers_mapping=get_dispatcher(),
        )[1].result["result"]

    return Result(host=task.host, result=result)


def config_provision(
    nautobot_job: Job,
    data: Dict,
):
    """Nornir play that pushes a configuration to a device.

    Args:
        job_result (Job): Job result.
        data (Dict): Dictionary with form data from the job that the play is being ran.
        config (str): Candidate configuration.
        dry_run (bool): Dry run option that gives a diff between running and candidate config.
    """
    now = datetime.now()
    logger = NornirLogger(__name__, nautobot_job, data.get("debug"))
    dry_run = data.get("dry_run", True)
    remove_regex_dict = {}
    for regex in ConfigRemove.objects.all():
        if not remove_regex_dict.get(regex.platform.slug) or "Remove" not in regex.name:
            remove_regex_dict[regex.platform.slug] = []
        remove_regex_dict[regex.platform.slug].append({"regex": regex.regex})

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

            nr_with_processors.run(
                task=run_provisioning,
                name="PROVISION CONFIG",
                logger=logger,
                dry_run=dry_run,
                remove_regex_dict=remove_regex_dict,
                nautobot_job=nautobot_job,
            )
            logger.log_debug("Completed configuration provisioning to devices.")

    except Exception as err:
        logger.log_failure(None, err)
        raise
