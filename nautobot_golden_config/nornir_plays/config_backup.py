"""Nornir job for backing up actual config."""
# pylint: disable=relative-beyond-top-level
import os

from datetime import datetime
from nornir import InitNornir
from nornir.core.task import Result, Task
from nornir.core.plugins.inventory import InventoryPluginRegister

from nornir_nautobot.plugins.tasks.dispatcher import dispatcher
from nornir_nautobot.utils.logger import NornirLogger

from nautobot_plugin_nornir.plugins.inventory.nautobot_orm import NautobotORMInventory
from nautobot_plugin_nornir.constants import NORNIR_SETTINGS

from nautobot_golden_config.utilities.helper import get_allowed_os, verify_global_settings, check_jinja_template
from nautobot_golden_config.models import GoldenConfigSettings, GoldenConfiguration
from .processor import ProcessGoldenConfig

InventoryPluginRegister.register("nautobot-inventory", NautobotORMInventory)


def get_substitute_lines(text):
    """Helper functionality to split on filter."""
    substitute_lines = []
    for line in text.splitlines():
        regex_replacement, regex_search = line.split("|||")
        substitute_lines.append({"regex_replacement": regex_replacement, "regex_search": regex_search})
    return substitute_lines


def run_backup(task: Task, logger, global_settings, backup_root_folder) -> Result:
    """Backup configurations to disk.

    Args:
        task (Task): Nornir task individual object

    Returns:
        result (Result): Result from Nornir task
    """
    obj = task.host.data["obj"]

    backup_obj = GoldenConfiguration.objects.filter(device=obj).first()
    if not backup_obj:
        backup_obj = GoldenConfiguration.objects.create(
            device=obj,
        )
    backup_obj.backup_last_attempt_date = task.host.defaults.data["now"]
    backup_obj.save()

    backup_path_template_obj = check_jinja_template(obj, logger, global_settings.backup_path_template)
    backup_file = os.path.join(backup_root_folder, backup_path_template_obj)
    substitute_lines = get_substitute_lines(global_settings.substitute_lines)

    if global_settings.backup_test_connectivity is not False:
        task.run(
            task=dispatcher,
            name="TEST CONNECTIVITY",
            method="check_connectivity",
            obj=obj,
            logger=logger,
        )
    running_config = task.run(
        task=dispatcher,
        name="SAVE BACKUP CONFIGURATION TO FILE",
        method="get_config",
        obj=obj,
        logger=logger,
        backup_file=backup_file,
        remove_lines=global_settings.remove_lines.splitlines(),
        substitute_lines=substitute_lines,
    )[1].result["config"]

    backup_obj.backup_last_success_date = task.host.defaults.data["now"]
    backup_obj.backup_config = running_config
    backup_obj.save()
    logger.log_success(obj, "Successfully backed up device.")

    return Result(host=task.host, result=running_config)


def config_backup(job_result, data, backup_root_folder):
    """Nornir play to backup configurations."""
    now = datetime.now()
    logger = NornirLogger(__name__, job_result, data.get("debug"))
    global_settings = GoldenConfigSettings.objects.get(id="aaaaaaaa-0000-0000-0000-000000000001")
    verify_global_settings(logger, global_settings, ["backup_path_template", "intended_path_template"])
    nornir_obj = InitNornir(
        runner=NORNIR_SETTINGS.get("runner"),
        logging={"enabled": False},
        inventory={
            "plugin": "nautobot-inventory",
            "options": {
                "credentials_class": NORNIR_SETTINGS.get("credentials"),
                "params": NORNIR_SETTINGS.get("inventory_params"),
                "queryset": get_allowed_os(data),
                "defaults": {"now": now},
            },
        },
    )

    nr_with_processors = nornir_obj.with_processors([ProcessGoldenConfig(logger)])

    nr_with_processors.run(
        task=run_backup,
        name="BACKUP CONFIG",
        logger=logger,
        global_settings=global_settings,
        backup_root_folder=backup_root_folder,
    )

    logger.log_debug("Completed configuration from devices.")
