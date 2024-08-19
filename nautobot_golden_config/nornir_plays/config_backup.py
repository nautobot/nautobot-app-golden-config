"""Nornir job for backing up actual config."""

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

from nautobot_golden_config.exceptions import BackupFailure
from nautobot_golden_config.models import ConfigRemove, ConfigReplace, GoldenConfig
from nautobot_golden_config.nornir_plays.processor import ProcessGoldenConfig
from nautobot_golden_config.utilities.db_management import close_threaded_db_connections
from nautobot_golden_config.utilities.helper import (
    dispatch_params,
    render_jinja_template,
    verify_settings,
)
from nautobot_golden_config.utilities.logger import NornirLogger

InventoryPluginRegister.register("nautobot-inventory", NautobotORMInventory)


@close_threaded_db_connections  # TODO: Is this still needed?
def run_backup(  # pylint: disable=too-many-arguments
    task: Task, logger: logging.Logger, device_to_settings_map, remove_regex_dict, replace_regex_dict
) -> Result:
    r"""Backup configurations to disk.

    Args:
        task (Task): Nornir task individual object
        remove_regex_dict (dict): {'cisco_ios': ['^Building\\s+configuration.*\\n', '^Current\\s+configuration.*\\n', '^!\\s+Last\\s+configuration.*'], 'arista_eos': ['.s*']}
        replace_regex_dict (dict): {'cisco_ios': [{'regex_replacement': '<redacted_config>', 'regex_search': 'username\\s+\\S+\\spassword\\s+5\\s+(\\S+)\\s+role\\s+\\S+'}]}

    Returns:
        result (Result): Result from Nornir task
    """
    obj = task.host.data["obj"]
    settings = device_to_settings_map[obj.id]

    backup_obj = GoldenConfig.objects.filter(device=obj).first()
    if not backup_obj:
        backup_obj = GoldenConfig.objects.create(
            device=obj,
        )
    backup_obj.backup_last_attempt_date = task.host.defaults.data["now"]
    backup_obj.save()

    backup_directory = settings.backup_repository.filesystem_path
    backup_path_template_obj = render_jinja_template(obj, logger, settings.backup_path_template)
    backup_file = os.path.join(backup_directory, backup_path_template_obj)

    if settings.backup_test_connectivity is not False:
        task.run(
            task=dispatcher,
            logger=logger,
            obj=obj,
            name="TEST CONNECTIVITY",
            **dispatch_params("check_connectivity", obj.platform.network_driver, logger),
        )
    running_config = task.run(
        task=dispatcher,
        obj=obj,
        logger=logger,
        name="SAVE BACKUP CONFIGURATION TO FILE",
        backup_file=backup_file,
        remove_lines=remove_regex_dict.get(obj.platform.network_driver, []),
        substitute_lines=replace_regex_dict.get(obj.platform.network_driver, []),
        **dispatch_params("get_config", obj.platform.network_driver, logger),
    )[1].result["config"]

    backup_obj.backup_last_success_date = task.host.defaults.data["now"]
    backup_obj.backup_config = running_config
    backup_obj.save()

    logger.info("Successfully extracted running configuration from device.", extra={"object": obj})

    return Result(host=task.host, result=running_config)


def config_backup(job):
    """
    Nornir play to backup configurations.

    Args:
        job (Job): The Nautobot Job instance being run.

    Returns:
        None: Backup configuration files are written to filesystem.

    Raises:
        BackupFailure: If failure found in Nornir tasks then Exception will be raised.
    """
    now = make_aware(datetime.now())
    logger = NornirLogger(job.job_result, job.logger.getEffectiveLevel())

    for settings in set(job.device_to_settings_map.values()):
        verify_settings(logger, settings, ["backup_path_template"])

    # Build a dictionary, with keys of platform.network_driver, and the regex line in it for the netutils func.
    remove_regex_dict = {}
    for regex in ConfigRemove.objects.all():
        if not remove_regex_dict.get(regex.platform.network_driver):
            remove_regex_dict[regex.platform.network_driver] = []
        remove_regex_dict[regex.platform.network_driver].append({"regex": regex.regex})

    # Build a dictionary, with keys of platform.network_driver, and the regex and replace keys for the netutils func.
    replace_regex_dict = {}
    for regex in ConfigReplace.objects.all():
        if not replace_regex_dict.get(regex.platform.network_driver):
            replace_regex_dict[regex.platform.network_driver] = []
        replace_regex_dict[regex.platform.network_driver].append({"replace": regex.replace, "regex": regex.regex})
    try:
        with InitNornir(
            runner=NORNIR_SETTINGS.get("runner"),
            logging={"enabled": False},
            inventory={
                "plugin": "nautobot-inventory",
                "options": {
                    "credentials_class": NORNIR_SETTINGS.get("credentials"),
                    "params": NORNIR_SETTINGS.get("inventory_params"),
                    "queryset": job.qs,
                    "defaults": {"now": now},
                },
            },
        ) as nornir_obj:
            nr_with_processors = nornir_obj.with_processors([ProcessGoldenConfig(logger)])

            logger.debug("Run nornir backup tasks.")
            results = nr_with_processors.run(
                task=run_backup,
                name="BACKUP CONFIG",
                logger=logger,
                device_to_settings_map=job.device_to_settings_map,
                remove_regex_dict=remove_regex_dict,
                replace_regex_dict=replace_regex_dict,
            )
            logger.debug("Completed configuration from devices.")
    except NornirNautobotException as err:
        logger.error(
            f"`E3027:` NornirNautobotException raised during backup tasks. Original exception message: ```{err}```"
        )
        # re-raise Exception if it's raised from nornir-nautobot or nautobot-app-nornir
        if str(err).startswith("`E2") or str(err).startswith("`E1"):
            raise NornirNautobotException(err) from err
    logger.debug("Completed configuration backup job for devices.")
    if results.failed:
        raise BackupFailure()
