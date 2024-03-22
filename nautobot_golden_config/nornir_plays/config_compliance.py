"""Nornir job for generating the compliance data."""
# pylint: disable=relative-beyond-top-level
import difflib
import logging
import os
from collections import defaultdict
from datetime import datetime

from nautobot_plugin_nornir.constants import NORNIR_SETTINGS
from nautobot_plugin_nornir.plugins.inventory.nautobot_orm import NautobotORMInventory
from netutils.config.compliance import _open_file_config, parser_map, section_config
from netutils.lib_mapper import NETUTILSPARSER_LIB_MAPPER_REVERSE
from nornir import InitNornir
from nornir.core.plugins.inventory import InventoryPluginRegister
from nornir.core.task import Result, Task
from nornir_nautobot.exceptions import NornirNautobotException
from nornir_nautobot.utils.logger import NornirLogger

from nautobot_golden_config.choices import ComplianceRuleConfigTypeChoice
from nautobot_golden_config.models import ComplianceRule, ConfigCompliance, GoldenConfig
from nautobot_golden_config.nornir_plays.processor import ProcessGoldenConfig
from nautobot_golden_config.utilities.db_management import close_threaded_db_connections
from nautobot_golden_config.utilities.helper import (
    get_device_to_settings_map,
    get_job_filter,
    get_json_config,
    render_jinja_template,
    verify_settings,
)
from nautobot_golden_config.utilities.utils import get_platform

InventoryPluginRegister.register("nautobot-inventory", NautobotORMInventory)
LOGGER = logging.getLogger(__name__)


def get_rules():
    """A serializer of sorts to return rule mappings as a dictionary."""
    # TODO: Review if creating a proper serializer is the way to go.
    rules = defaultdict(list)
    for compliance_rule in ComplianceRule.objects.all():
        platform = str(compliance_rule.platform.slug)
        rules[platform].append(
            {
                "ordered": compliance_rule.config_ordered,
                "obj": compliance_rule,
                "section": compliance_rule.match_config.splitlines(),
            }
        )
    return rules


def get_config_element(rule, config, obj, logger):
    """
    Helper function to yield elements of the configuration as defined in the `config_match` under ComplianceRule.

    Returns:
       - a configuration section for `CLI` based config types
       - top level JSON key for `JSON` based config types
    """
    if rule["obj"].config_type == ComplianceRuleConfigTypeChoice.TYPE_JSON:
        config_json = get_json_config(config)

        if not config_json:
            logger.log_failure(obj, "Unable to interpret configuration as JSON.")
            raise NornirNautobotException("Unable to interpret configuration as JSON.")

        if rule["obj"].match_config:
            config_element = {k: config_json.get(k) for k in rule["obj"].match_config.splitlines() if k in config_json}
        else:
            config_element = config_json

    elif rule["obj"].config_type == ComplianceRuleConfigTypeChoice.TYPE_CLI:
        _platform_slug = get_platform(obj.platform.slug)
        netutils_os_parser = NETUTILSPARSER_LIB_MAPPER_REVERSE.get(_platform_slug, _platform_slug)
        if netutils_os_parser not in parser_map.keys():
            logger.log_failure(
                obj,
                f"There is currently no CLI-config parser support for platform slug `{netutils_os_parser}`, preemptively failed.",
            )
            raise NornirNautobotException(
                f"There is currently no CLI-config parser support for platform slug `{netutils_os_parser}`, preemptively failed."
            )

        config_element = section_config(rule, config, netutils_os_parser)

    else:
        logger.log_failure(obj, f"There rule type ({rule['obj'].config_type}) is not recognized.")
        raise NornirNautobotException(f"There rule type ({rule['obj'].config_type}) is not recognized.")

    return config_element


def diff_files(backup_file, intended_file):
    """Utility function to provide `Unix Diff` between two files."""
    bkup = open(backup_file).readlines()
    intended = open(intended_file).readlines()

    for line in difflib.unified_diff(bkup, intended, lineterm=""):
        yield line


@close_threaded_db_connections
def run_compliance(  # pylint: disable=too-many-arguments,too-many-locals
    task: Task,
    logger,
    device_to_settings_map,
    rules,
) -> Result:
    """Prepare data for compliance task.

    Args:
        task (Task): Nornir task individual object

    Returns:
        result (Result): Result from Nornir task
    """
    obj = task.host.data["obj"]
    settings = device_to_settings_map[obj.id]

    compliance_obj = GoldenConfig.objects.filter(device=obj).first()
    if not compliance_obj:
        compliance_obj = GoldenConfig.objects.create(device=obj)
    compliance_obj.compliance_last_attempt_date = task.host.defaults.data["now"]
    compliance_obj.save()

    intended_directory = settings.intended_repository.filesystem_path
    intended_path_template_obj = render_jinja_template(obj, logger, settings.intended_path_template)
    intended_file = os.path.join(intended_directory, intended_path_template_obj)

    if not os.path.exists(intended_file):
        logger.log_failure(obj, f"Unable to locate intended file for device at {intended_file}, preemptively failed.")
        raise NornirNautobotException(
            f"Unable to locate intended file for device at {intended_file}, preemptively failed."
        )

    backup_directory = settings.backup_repository.filesystem_path
    backup_template = render_jinja_template(obj, logger, settings.backup_path_template)
    backup_file = os.path.join(backup_directory, backup_template)

    if not os.path.exists(backup_file):
        logger.log_failure(obj, f"Unable to locate backup file for device at {backup_file}, preemptively failed.")
        raise NornirNautobotException(f"Unable to locate backup file for device at {backup_file}, preemptively failed.")

    platform = obj.platform.slug
    if not rules.get(platform):
        logger.log_failure(
            obj, f"There is no defined `Configuration Rule` for platform slug `{platform}`, preemptively failed."
        )
        raise NornirNautobotException(
            f"There is no defined `Configuration Rule` for platform slug `{platform}`, preemptively failed."
        )

    backup_cfg = _open_file_config(backup_file)
    intended_cfg = _open_file_config(intended_file)

    for rule in rules[obj.platform.slug]:
        _actual = get_config_element(rule, backup_cfg, obj, logger)
        _intended = get_config_element(rule, intended_cfg, obj, logger)

        # using update_or_create() method to conveniently update actual obj or create new one.
        ConfigCompliance.objects.update_or_create(
            device=obj,
            rule=rule["obj"],
            defaults={
                "actual": _actual,
                "intended": _intended,
                "missing": "",
                "extra": "",
            },
        )

    compliance_obj.compliance_last_success_date = task.host.defaults.data["now"]
    compliance_obj.compliance_config = "\n".join(diff_files(backup_file, intended_file))
    compliance_obj.save()
    logger.log_success(obj, "Successfully tested compliance job.")

    return Result(host=task.host)


def config_compliance(job_result, data):
    """Nornir play to generate configurations."""
    now = datetime.now()
    rules = get_rules()
    logger = NornirLogger(__name__, job_result, data.get("debug"))

    qs = get_job_filter(data)
    logger.log_debug("Compiling device data for compliance job.")
    device_to_settings_map = get_device_to_settings_map(queryset=qs)

    for settings in set(device_to_settings_map.values()):
        verify_settings(logger, settings, ["backup_path_template", "intended_path_template"])

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

            logger.log_debug("Run nornir compliance tasks.")
            nr_with_processors.run(
                task=run_compliance,
                name="RENDER COMPLIANCE TASK GROUP",
                logger=logger,
                device_to_settings_map=device_to_settings_map,
                rules=rules,
            )

    except Exception as err:
        logger.log_failure(None, err)
        raise

    logger.log_debug("Completed compliance job for devices.")
