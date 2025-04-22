"""Nornir job for generating the compliance data."""

# pylint: disable=relative-beyond-top-level
import hier_config

import difflib
import logging
import os
import yaml
import hashlib
import json
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
        hier_config_rule = False
        dunder_config_rule = False

        # Check for hier config compliance rule
        section_type = rule["section"][0]
        if "# hier_config" in section_type:
            hier_config_rule = True
            
        # Check for nested config to match defined with a double underscore, e.g. 'interface__service-policy'
        if not hier_config_rule:
            for section in rule["section"]:
                if "__" in section:
                    dunder_config_rule = True
                    break

        if hier_config_rule:
            _actual, _intended = process_nested_compliance_rule_hier_config(rule, backup_cfg, intended_cfg, obj, logger)
        elif dunder_config_rule:
            _actual, _intended = process_nested_compliance_rule_dunder(rule, backup_cfg, intended_cfg, obj, logger)
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

def process_nested_compliance_rule_hier_config(rule, backup_cfg, intended_cfg, obj, logger):
    """Process nested compliance rules using hierarchical configuration comparison.

    This function processes compliance rules by comparing backup (running) and intended configurations
    using hierarchical config parsing. It filters the configs based on specified match criteria and tags.

    Args:
        rule (dict): Dictionary containing compliance rule details including match configuration
        backup_cfg (str): The backup/running configuration text
        intended_cfg (str): The intended/generated configuration text
        obj (obj): Object containing platform and device information

    Returns:
        tuple: A tuple containing:
            - running_text (str): Filtered running configuration text
            - intended_text (str): Filtered intended configuration text

    The function:
    1. Creates a hierarchical config host object
    2. Loads running and intended configs
    3. Applies matching rules and tags from the compliance rule
    4. Filters both configs by the specified tags
    5. Returns the filtered configs for comparison

    The match_config in the rule should define the hierarchical config tags and matching criteria
    in YAML format.

    More information can be found in the Hier Config documentation:
    https://hier-config.readthedocs.io/en/2.3-lts/advanced-topics/#working-with-tags

    """
    os = obj.platform.network_driver_mappings["hier_config"]

    # Create host object and load configs
    host = hier_config.Host(hostname=obj.name, os=os)
    host.load_running_config(backup_cfg)
    host.load_generated_config(intended_cfg)

    match_config = yaml.safe_load(rule["obj"].match_config)
    host.load_tags(match_config)
    tag_names = set()
    for lineage in match_config:
        # Create a unique tag name for each lineage
        tag_name = hashlib.sha1(json.dumps(lineage, sort_keys=True).encode()).hexdigest() # noqa: S324
        lineage["add_tags"] = tag_name
        tag_names.add(tag_name)

    host.running_config.add_tags(host._hconfig_tags)
    host.generated_config.add_tags(host._hconfig_tags)

    # Concatonate actual config, filtered by tags
    running_config_generator = host.running_config.all_children_sorted_by_tags(tag_names, set())
    running_text = "\n".join(c.cisco_style_text() for c in running_config_generator)
    # Concatonate intended config, filtered by tags
    intended_config_generator = host.generated_config.all_children_sorted_by_tags(tag_names, set())
    intended_text = "\n".join(c.cisco_style_text() for c in intended_config_generator)

    return running_text, intended_text

def get_full_lines(
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
    nested_sections_to_match: list,
    device_cfg: str,
    network_os: str,
) -> str:
    """Extract configuration sections that exactly match specified criteria.

    This function parses device configuration and extracts sections that exactly match
    given criteria, excluding lines that do not contain strings matching those in nested_sections_to_match.
    Args:
        feature (Dict[str, Union[str, bool, List[str]]]): Dictionary containing configuration
            matching criteria. Must include 'section' key with string or list of strings
            to match section starts.
        nested_sections_to_match (str): String or sequence of nested section identifiers
            to match within the main section.
        device_cfg (str): Complete device configuration as a string.
        network_os (str): Network operating system identifier to determine appropriate parser.
    Returns:
        str: Extracted configuration sections joined by newlines. Returns empty string if
            no matches found. Returns original config if no section criteria specified.
    """
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
                for nested_section_to_match in nested_sections_to_match:
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

def process_nested_compliance_rule_dunder(rule, backup_cfg, intended_cfg, obj, logger):
    """Process nested compliance rules for network device configurations.

    This function handles the processing of nested compliance rules, specifically for CLI config types.
    It compares backup (actual) and intended configurations for nested sections within a top-level
    configuration block (e.g., interface configurations with nested service policies or LLDP settings).
    Args:
        rule (dict): Dictionary containing compliance rule details including:
            - obj: Compliance rule object with config_type attribute
            - section: List of sections to check in format "top_level__nested" 
        backup_cfg (str): The actual/backup configuration to check
        intended_cfg (str): The intended/golden configuration to compare against
        obj: Device object containing platform information
        logger: Logger object for error reporting
    Returns:
        tuple: A tuple containing:
            - str: Actual configuration block matching the nested rule
            - str: Intended configuration block matching the nested rule
    Raises:
        NornirNautobotException: If rule is not CLI type or contains multiple top-level sections
    Example sections format:
        Valid:
            - ["interface__lldp", "interface__service-policy"]
        Invalid:
            - ["dns__hostname", "interface__service-policy"]
    Notes:
        - Only supports CLI config types
        - All nested sections must share the same top-level section
        - Returns concatenated configuration blocks for all matching sections
    """

    #TODO: REMOVE THESE TESITNG ELEMENTS
    # interfaces = ["interface GigabitEthernet0/0", "interface GigabitEthernet2/0/1", "interface GigabitEthernet2/0/2", "interface GigabitEthernet2/0/3", "interface GigabitEthernet2/0/4", "interface GigabitEthernet2/0/5", "interface GigabitEthernet2/0/6", "interface GigabitEthernet2/0/7", "interface GigabitEthernet2/0/8", "interface GigabitEthernet2/0/9", "interface GigabitEthernet2/0/10", "interface GigabitEthernet2/0/11", "interface GigabitEthernet2/0/12", "interface GigabitEthernet2/0/13", "interface GigabitEthernet2/0/14", "interface GigabitEthernet2/0/15", "interface GigabitEthernet2/0/16", "interface GigabitEthernet2/0/17", "interface GigabitEthernet2/0/18", "interface GigabitEthernet2/0/19", "interface GigabitEthernet2/0/20", "interface GigabitEthernet2/0/21", "interface GigabitEthernet2/0/22", "interface GigabitEthernet2/0/23", "interface GigabitEthernet2/0/24", "interface GigabitEthernet2/1/1", "interface GigabitEthernet2/1/2", "interface GigabitEthernet2/1/3", "interface GigabitEthernet2/1/4", "interface TenGigabitEthernet2/1/1", "interface TenGigabitEthernet2/1/2", "interface TenGigabitEthernet2/1/3", "interface TenGigabitEthernet2/1/4", "interface Loopback103", "interface Port-channel1", "interface Vlan1", "interface Vlan100", "interface Vlan999", "interface Vlan3301", "interface Vlan4060", "interface Vlan4070", "interface Vlan4080", "interface Vlan4090"]
    # intended_cfg = ""
    # for interface in interfaces:
    #     intended_cfg = intended_cfg + interface + "\n service-policy input ACCESS_IN\n service-policy output ACCESS_OUT\n no lldp transmit\n"
    # backup_cfg = ""
    # for interface in interfaces:
    #     backup_cfg = backup_cfg + interface + "\n service-policy input ACCESS_IN\n service-policy output ACCESS_OUT\n lldp transmit\n"

    _actual = ""
    _intended = ""

    # Check if the compliance rule is of type CLI
    if rule["obj"].config_type != ComplianceRuleConfigTypeChoice.TYPE_CLI:
        error_msg = "`E3008:` Nested compliance rules are only supported for CLI config types."
        logger.error(error_msg, extra={"object": obj})
        raise NornirNautobotException(error_msg)
    
    # Create a list of top level sections, a valid compliance rule will only have 1 entry, i.e. ["interface"]
    # Create a list of nested sections to match i.e. ["service-policy", "lldp"]
    top_level_section_list = []
    nested_sections_to_match = []
    for section in rule["section"]:
        if "__" not in section:
            error_msg = (
                f"`E3010:` Nested compliance rules must contain a nested section to match. "
                f"Config to match '{section}' is invalid."
            )
            logger.error(error_msg, extra={"object": obj})
            raise NornirNautobotException(error_msg)
        top_level_section = section.split("__")[0]
        if top_level_section not in top_level_section_list:
            top_level_section_list.append(top_level_section)
        nested_section = section.split("__")[1]
        if nested_section not in nested_sections_to_match:
            nested_sections_to_match.append(nested_section)

    # If there are multiple top level sections, raise an error.
    # In config to match:
    #
    # this is valid:
    # interface__lldp 
    # interface__service-policy
    #
    # this is invalid: 
    # dns__hostname
    # interface__service-policy
    if len(top_level_section_list) > 1:
        error_detail = f"{rule['obj'].feature} contains the following top level sections: {top_level_section_list}"
        error_msg = f"`E3009:` Nested compliance rules do not support multiple top level sections within the same rule. {error_detail}"
        logger.error(error_msg, extra={"object": obj})
        raise NornirNautobotException(error_msg)

    # The first part of a nested section is the top level secton to match and will be used to find whole lines that need to match exactly.
    # For example, 'interface' will find all lines starting with 'interface' that do not have a parent and return each full line, e.g. 'interface GigabitEthernet1/0/2'
    rule["section"] = [top_level_section_list[0]]
    actual_top_level_lines_to_match = get_full_lines(rule, backup_cfg, obj.platform.network_driver_mappings["netutils_parser"])
    intended_top_level_lines_to_match = get_full_lines(rule, intended_cfg, obj.platform.network_driver_mappings["netutils_parser"])
                
    # Each full line is used to match the config element for the nested section. 
    # These config elements are then filtered to exclude any lines that do not include the second
    # part of the nested section. For example, 'inteface__service-policy' will filter out any lines 
    # from the small section of matched config that do not contain 'service-policy' with the assumption 
    # they should not be considered for compliance.
    # These filtered config elements are concatonated to create a single block for compliance checking.
    for line in actual_top_level_lines_to_match:
        rule["section"] = [line]
        actual_config_element = section_config_exact_match(rule, nested_sections_to_match, backup_cfg, obj.platform.network_driver_mappings["netutils_parser"])
        if _actual:
            _actual = _actual  + "\n" +  actual_config_element
        else:
            _actual = actual_config_element

    for line in intended_top_level_lines_to_match:
        rule["section"] = [line]
        intended_config_element = section_config_exact_match(rule, nested_sections_to_match, intended_cfg, obj.platform.network_driver_mappings["netutils_parser"])
        if _intended:
            _intended = _intended + "\n" +  intended_config_element
        else:
            _intended = intended_config_element

    return _actual, _intended

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
