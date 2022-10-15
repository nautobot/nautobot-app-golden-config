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
from nautobot_plugin_nornir.utils import get_dispatcher

from nautobot_golden_config.utilities.db_management import close_threaded_db_connections
from nautobot_golden_config.utilities.helper import (
    get_device_to_settings_map,
    get_job_filter,
    verify_settings,
    render_jinja_template,
)
from nautobot_golden_config.models import (
    GoldenConfig,
    ConfigRemove,
    ConfigReplace,
)
from nautobot_golden_config.nornir_plays.processor import ProcessGoldenConfig

InventoryPluginRegister.register("nautobot-inventory", NautobotORMInventory)


@close_threaded_db_connections
def run_backup(  # pylint: disable=too-many-arguments
    task: Task, logger, device_to_settings_map, remove_regex_dict, replace_regex_dict
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
            name="TEST CONNECTIVITY",
            method="check_connectivity",
            obj=obj,
            logger=logger,
            default_drivers_mapping=get_dispatcher(),
        )
    running_config = task.run(
        task=dispatcher,
        name="SAVE BACKUP CONFIGURATION TO FILE",
        method="get_config",
        obj=obj,
        logger=logger,
        backup_file=backup_file,
        remove_lines=remove_regex_dict.get(obj.platform.slug, []),
        substitute_lines=replace_regex_dict.get(obj.platform.slug, []),
        default_drivers_mapping=get_dispatcher(),
    )[1].result["config"]

    backup_obj.backup_last_success_date = task.host.defaults.data["now"]
    backup_obj.backup_config = running_config
    backup_obj.save()

    logger.log_success(obj, "Successfully extracted running configuration from device.")

    return Result(host=task.host, result=running_config)


def config_backup(job_result, data):
    """Nornir play to backup configurations."""
    now = datetime.now()
    logger = NornirLogger(__name__, job_result, data.get("debug"))

    qs = get_job_filter(data)
    logger.log_debug("Compiling device data for backup.")
    device_to_settings_map = get_device_to_settings_map(queryset=qs)

    for settings in set(device_to_settings_map.values()):
        verify_settings(logger, settings, ["backup_path_template"])

    # Build a dictionary, with keys of platform.slug, and the regex line in it for the netutils func.
    remove_regex_dict = {}
    for regex in ConfigRemove.objects.all():
        if not remove_regex_dict.get(regex.platform.slug):
            remove_regex_dict[regex.platform.slug] = []
        remove_regex_dict[regex.platform.slug].append({"regex": regex.regex})

    # Build a dictionary, with keys of platform.slug, and the regex and replace keys for the netutils func.
    replace_regex_dict = {}
    for regex in ConfigReplace.objects.all():
        if not replace_regex_dict.get(regex.platform.slug):
            replace_regex_dict[regex.platform.slug] = []
        replace_regex_dict[regex.platform.slug].append({"replace": regex.replace, "regex": regex.regex})
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

            logger.log_debug("Run nornir backup tasks.")
            nr_with_processors.run(
                task=run_backup,
                name="BACKUP CONFIG",
                logger=logger,
                device_to_settings_map=device_to_settings_map,
                remove_regex_dict=remove_regex_dict,
                replace_regex_dict=replace_regex_dict,
            )
            logger.log_debug("Completed configuration from devices.")

    except Exception as err:
        logger.log_failure(None, err)
        raise

    logger.log_debug("Completed configuration backup job for devices.")
