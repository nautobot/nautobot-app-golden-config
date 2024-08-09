"""Nornir job for generating the compliance data."""

# pylint: disable=relative-beyond-top-level
import difflib
import logging
import os
from collections import defaultdict
from datetime import datetime

from django.utils.timezone import make_aware
from lxml import etree
from nautobot_plugin_nornir.constants import NORNIR_SETTINGS
from nautobot_plugin_nornir.plugins.inventory.nautobot_orm import NautobotORMInventory
from netutils.config.compliance import _open_file_config, parser_map, section_config
from nornir import InitNornir
from nornir.core.plugins.inventory import InventoryPluginRegister
from nornir.core.task import Result, Task
from nornir_nautobot.exceptions import NornirNautobotException

from nautobot_golden_config.choices import ComplianceRuleConfigTypeChoice
from nautobot_golden_config.exceptions import ComplianceFailure
from nautobot_golden_config.models import ComplianceRule, ConfigCompliance, GoldenConfig
from nautobot_golden_config.nornir_plays.processor import ProcessGoldenConfig
from nautobot_golden_config.utilities.db_management import close_threaded_db_connections
from nautobot_golden_config.utilities.helper import (
    get_json_config,
    get_xml_config,
    get_xml_subtree_with_full_path,
    render_jinja_template,
    verify_settings,
)
from nautobot_golden_config.utilities.logger import NornirLogger

InventoryPluginRegister.register("nautobot-inventory", NautobotORMInventory)
LOGGER = logging.getLogger(__name__)


def get_rules():
    """A serializer of sorts to return rule mappings as a dictionary."""
    # TODO: Future: Review if creating a proper serializer is the way to go.
    rules = defaultdict(list)
    for compliance_rule in ComplianceRule.objects.all():
        platform = str(compliance_rule.platform.network_driver)
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
            error_msg = "`E3002:` Unable to interpret configuration as JSON."
            logger.error(error_msg, extra={"object": obj})
            raise NornirNautobotException(error_msg)

        if rule["obj"].match_config:
            config_element = {k: config_json.get(k) for k in rule["obj"].match_config.splitlines() if k in config_json}
        else:
            config_element = config_json

    elif rule["obj"].config_type == ComplianceRuleConfigTypeChoice.TYPE_XML:
        config_xml = get_xml_config(config)

        if not config_xml:
            error_msg = "`E3002:` Unable to interpret configuration as XML."
            logger.error(error_msg, extra={"object": obj})
            raise NornirNautobotException(error_msg)

        if rule["obj"].match_config:
            try:
                config_element = get_xml_subtree_with_full_path(config_xml, rule["obj"].match_config)
            except etree.XPathError as err:
                error_msg = f"`E3031:` Invalid XPath expression - `{rule['obj'].match_config}`"
                logger.error(error_msg, extra={"object": obj})
                raise NornirNautobotException(error_msg) from err
        else:
            config_element = etree.tostring(config_xml, encoding="unicode", pretty_print=True)

    elif rule["obj"].config_type == ComplianceRuleConfigTypeChoice.TYPE_CLI:
        if obj.platform.network_driver_mappings["netutils_parser"] not in parser_map:
            error_msg = f"`E3003:` There is currently no CLI-config parser support for platform network_driver `{obj.platform.network_driver}`, preemptively failed."
            logger.error(error_msg, extra={"object": obj})
            raise NornirNautobotException(error_msg)

        config_element = section_config(rule, config, obj.platform.network_driver_mappings["netutils_parser"])

    else:
        error_msg = f"`E3004:` There rule type ({rule['obj'].config_type}) is not recognized."
        logger.error(error_msg, extra={"object": obj})
        raise NornirNautobotException(error_msg)

    return config_element


def diff_files(backup_file, intended_file):
    """Utility function to provide `Unix Diff` between two files."""
    with open(backup_file, encoding="utf-8") as file:
        backup = file.readlines()
    with open(intended_file, encoding="utf-8") as file:
        intended = file.readlines()

    yield from difflib.unified_diff(backup, intended, lineterm="")


@close_threaded_db_connections
def run_compliance(  # pylint: disable=too-many-arguments,too-many-locals
    task: Task,
    logger: logging.Logger,
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
        error_msg = f"`E3005:` Unable to locate intended file for device at {intended_file}, preemptively failed."
        logger.error(error_msg, extra={"object": obj})
        raise NornirNautobotException(error_msg)

    backup_directory = settings.backup_repository.filesystem_path
    backup_template = render_jinja_template(obj, logger, settings.backup_path_template)
    backup_file = os.path.join(backup_directory, backup_template)

    if not os.path.exists(backup_file):
        error_msg = f"`E3006:` Unable to locate backup file for device at {backup_file}, preemptively failed."
        logger.error(error_msg, extra={"object": obj})
        raise NornirNautobotException(error_msg)

    platform = obj.platform.network_driver
    if not rules.get(platform):
        error_msg = (
            f"`E3007:` There is no defined `Configuration Rule` for platform network_driver `{platform}`, "
            "preemptively failed."
        )
        logger.error(error_msg, extra={"object": obj})
        raise NornirNautobotException(error_msg)

    backup_cfg = _open_file_config(backup_file)
    intended_cfg = _open_file_config(intended_file)

    for rule in rules[obj.platform.network_driver]:
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
    logger.info("Successfully tested compliance job.", extra={"object": obj})

    return Result(host=task.host)


def config_compliance(job):  # pylint: disable=unused-argument
    """
    Nornir play to generate configurations.

    Args:
        job (Job): The Nautobot Job instance being run.

    Returns:
        None: Compliance results are written to database.

    Raises:
        ComplianceFailure: If failure found in Nornir tasks then Exception will be raised.
    """
    now = make_aware(datetime.now())
    logger = NornirLogger(job.job_result, job.logger.getEffectiveLevel())

    rules = get_rules()

    for settings in set(job.device_to_settings_map.values()):
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
                    "queryset": job.qs,
                    "defaults": {"now": now},
                },
            },
        ) as nornir_obj:
            nr_with_processors = nornir_obj.with_processors([ProcessGoldenConfig(logger)])

            logger.debug("Run nornir compliance tasks.")
            results = nr_with_processors.run(
                task=run_compliance,
                name="RENDER COMPLIANCE TASK GROUP",
                logger=logger,
                device_to_settings_map=job.device_to_settings_map,
                rules=rules,
            )
    except NornirNautobotException as err:
        logger.error(
            f"`E3028:` NornirNautobotException raised during compliance tasks. Original exception message: ```{err}```"
        )
        # re-raise Exception if it's raised from nornir-nautobot or nautobot-app-nornir
        if str(err).startswith("`E2") or str(err).startswith("`E1"):
            raise NornirNautobotException(err) from err
    logger.debug("Completed compliance job for devices.")
    if results.failed:
        raise ComplianceFailure()
