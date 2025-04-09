"""Nornir job for generating the compliance data."""

# pylint: disable=relative-beyond-top-level
import difflib
import logging
import os
from collections import defaultdict
from datetime import datetime
import typing as t

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
        rule_contains_nested_config = False
        for section in rule["section"]:
            if "__" in section:
                rule_contains_nested_config = True
                break
        if rule_contains_nested_config:
            _actual, _intended = process_nested_compliance_rule(rule, backup_cfg, intended_cfg, obj, logger)
        else:
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

def get_line_matches(
    feature: t.Dict[str, t.Union[str, bool, t.List[str]]],
    device_cfg: str,
    network_os: str,
):
    """
    Extracts configuration lines that match a specified section from device configuration.
    Args:
        feature (Dict[str, Union[str, bool, List[str]]]): Dictionary containing feature configuration parameters.
            Expected to have a 'section' key specifying the section to match.
        device_cfg (str): The complete device configuration text.
        network_os (str): The network operating system identifier used to determine the parser.
    Returns:
        str: List of configuration lines that match the specified section prefix.
            If no section is specified in the feature dictionary, returns the original device configuration.
    Raises:
        KeyError: If the network_os is not found in parser_map.
    Example:
        config input:

        interface GigabitEthernet1/0/2
        device-tracking attach-policy IPDT_MAX_10
        service-policy input INPUTVALUE
        service-policy output OUTPUTVALUE
        !
        interface GigabitEthernet1/0/3
        device-tracking attach-policy IPDT_MAX_10
        service-policy input INPUTVALUE
        service-policy output OUTPUTVALUE

        return:

        ["interface GigabitEthernet1/0/2", "interface GigabitEthernet1/0/3"]
    """
    section_starts_with = feature.get("section")
    if not section_starts_with:
        print(f"No lines match {feature.get('section')}")
        return device_cfg
    line_matches = []
    os_parser = parser_map[network_os]
    config_parsed = os_parser(device_cfg)

    for line in config_parsed.config_lines:
        if line.config_line.startswith(section_starts_with[0]):
            line_matches.append(line.config_line)
    return line_matches

def section_config_exact_match(
    feature: t.Dict[str, t.Union[str, bool, t.List[str]]],
    nested_section_to_match: str,
    device_cfg: str,
    network_os: str,
) -> str:
    section_starts_with = feature.get("section")
    if not section_starts_with:
        return device_cfg

    match = False
    section_config_list = []
    os_parser = parser_map[network_os]
    config_parsed = os_parser(device_cfg)
    for line in config_parsed.config_lines:
        # PROBABLY NOT NEEDED HERE
        # If multiple banners, line after first banner will be None.
        # This conditional allows multiple banners in config.
        # if not line.config_line:
        #     continue
        if match:
            if line.parents:
                if nested_section_to_match in line.config_line:
                    section_config_list.append(line.config_line)
                continue
            else:
                match = False
        for line_start in section_starts_with:  # type: ignore
            if not match and line.config_line == line_start:
                section_config_list.append(line.config_line)
                match = True
    return "\n".join(section_config_list).strip()

def process_nested_compliance_rule(rule, backup_cfg, intended_cfg, obj, logger):
    """
    Process nested compliance rule.

    Args:
        rule (dict): A dictionary containing the compliance rule.

    Returns:
        dict: The processed compliance rule.
    """
    _actual = ""
    _intended = ""
    if rule["obj"].config_type != ComplianceRuleConfigTypeChoice.TYPE_CLI:
        error_msg = "`E3008:` Nested compliance rules are only supported for CLI config types."
        logger.error(error_msg, extra={"object": obj})
        raise NornirNautobotException(error_msg)
    for section in rule["section"]:
            if "__" in section:
                section_list = section.split("__")
                rule["section"] = [section_list[0]]
                actual_top_level_lines_to_match = get_line_matches(rule, backup_cfg, obj.platform.network_driver_mappings["netutils_parser"])
                intended_top_level_lines_to_match = get_line_matches(rule, intended_cfg, obj.platform.network_driver_mappings["netutils_parser"])
                
                for line in actual_top_level_lines_to_match:
                    rule["section"] = [line]
                    # WARNING THIS BYPASSES THE CHECKS IN GET_CONFIG_ELEMENT -- fix it
                    nested_section_to_match = section_list[-1]
                    config_element = section_config_exact_match(rule, nested_section_to_match, backup_cfg, obj.platform.network_driver_mappings["netutils_parser"])
                    if _actual:
                        _actual = _actual  + "\n" +  config_element
                    else:
                        _actual = config_element

                for line in intended_top_level_lines_to_match:
                    rule["section"] = [line]
                    # WARNING THIS BYPASSES THE CHECKS IN GET_CONFIG_ELEMENT -- fix it
                    nested_section_to_match = section_list[-1]
                    config_element = section_config_exact_match(rule, nested_section_to_match, backup_cfg, obj.platform.network_driver_mappings["netutils_parser"])
                    if _intended:
                        _intended = _intended + "\n" +  config_element
                    else:
                        _intended = config_element
            else:
                # WARNING! This is intended to allow for mixing nested and non-nested sections in the same rule, but probably doesn't work.
                # May not even be necessasry. Maybe a compliance rule should only have one type of section (nested or non-nested).
                rule["section"] = [section]
                actual_config_element = get_config_element(rule, backup_cfg, obj, logger)
                if _actual:
                    _actual = _actual  + "\n" +  actual_config_element
                else:
                    _actual = config_element
                intended_config_element = get_config_element(rule, backup_cfg, obj, logger)
                if _intended:
                    _intended = _intended + "\n" +  intended_config_element
                else:
                    _intended = intended_config_element


    return _actual, _actual


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
