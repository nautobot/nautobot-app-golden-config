"""Error codes used in Stacktrace and generated docs."""

from collections import namedtuple

ErrorCode = namedtuple("ErrorCode", ["troubleshooting", "description", "error_message", "recommendation"])

ERROR_CODES = {
    "E3XXX": ErrorCode(
        troubleshooting="Find the error code in the traceback, and search for it in the codebase.",
        description="This means a code snippet was calling get_error_code() with an error code that is not registered.",
        error_message="Un-Registered Error Code used.",
        recommendation="Add the error code to the `error_codes.py` file.",
    ),
    "E3032": ErrorCode(
        troubleshooting="Check the YAML file for the `platform_slug` or `platform_network_driver` key. If it is not unique, then you need to use the `platform_name` key instead.",
        description="Syncing Golden Config properties using Datasource feature, but using non-unique key..",
        error_message="Reference to {yaml_attr_name}: {yaml_attr_value}, is not unique. Please use platform_name key instead.",
        recommendation="Migrate the YAML file keys from `platform_slug` or `platform_network_driver` to `platform_name`.",
    ),
    "E3033": ErrorCode(
        troubleshooting="The platform key used in the YAML file cannot be found.",
        description="Searching for the platform key in the YAML file and it cannot be found in the database.",
        error_message="Reference to {yaml_attr_name}: {yaml_attr_value} is not available.",
        recommendation="Check the YAML file for misspellings or incorrect values, if using `platform_slug` or `platform_network_driver`, then migrate to `platform_name` key instead.",
    ),
    "E3034": ErrorCode(
        troubleshooting="The tag referenced in the YAML file cannot be found for the relevant object type. Confirm the tag exists AND that its `content_types` includes the model being synced (the directory name maps to the model, e.g. compliance_rules -> ComplianceRule).",
        description="Syncing Golden Config properties using the Datasource feature, but a referenced tag does not exist or is not associated with the model's content type.",
        error_message="Reference to tag {tag_reference} is not available for {model}.",
        recommendation="Create the tag in Nautobot and associate it with the {model} content type before syncing, or correct the tag reference in the YAML file.",
    ),
    "E3035": ErrorCode(
        troubleshooting="Check the Network driver of the device's Platform, and the `hier_config` entry of its Network driver mappings.",
        description="Partial CLI compliance rules are matched with hier_config, but hier_config has no support for the platform's network driver.",
        error_message="There is currently no hier_config support for platform network_driver `{network_driver}`, required by Partial CLI compliance rules.",
        recommendation="Set the Platform's Network driver to one supported by hier_config, for example `cisco_ios`, `cisco_nxos` or `arista_eos`, or map the network driver to a supported hier_config platform with the `NETWORK_DRIVERS` setting.",
    ),
    "E3036": ErrorCode(
        troubleshooting="Check the Config to Match field of the Partial CLI compliance rule for YAML syntax errors, such as wrong indentation or unclosed brackets.",
        description="The Config to Match field of a Partial CLI compliance rule cannot be parsed as YAML.",
        error_message="Invalid YAML in the Partial CLI Config to Match: {error}",
        recommendation="Fix the YAML syntax of the Config to Match field. See the Partial Configuration Compliance documentation for examples.",
    ),
    "E3037": ErrorCode(
        troubleshooting="Check that the Config to Match field is a YAML list, and that each entry of the list is a mapping with a `match_rules` key.",
        description="The Config to Match field of a Partial CLI compliance rule is valid YAML, but not a non-empty list of rule blocks.",
        error_message="Invalid structure in the Partial CLI Config to Match, {details}.",
        recommendation="Start each rule block with `- match_rules:`, followed by its list of match rules. See the Partial Configuration Compliance documentation for examples.",
    ),
    "E3038": ErrorCode(
        troubleshooting="Check the rule block and field named in the error, for example a misspelled keyword such as `startwith`, or a rule block without `match_rules`.",
        description="hier_config rejected the match rules in the Config to Match field of a Partial CLI compliance rule.",
        error_message="Invalid hier_config match rules in the Partial CLI Config to Match: {details}",
        recommendation="Use only the `match_rules` key in each rule block, with the keywords `equals`, `startswith`, `endswith`, `contains` or `re_search`.",
    ),
    "E3039": ErrorCode(
        troubleshooting="Check the Remediation Options of the Remediation Settings of the device's Platform.",
        description="Partial CLI compliance parses configurations with the remediation options of the platform's Remediation Settings, and hier_config cannot load them.",
        error_message="Invalid remediation options in the Remediation Settings of platform `{platform}`: {error}",
        recommendation="Fix the Remediation Options so hier_config can load them, or clear them.",
    ),
}


def get_error_message(error_code, **kwargs):
    """Get the error message for a given error code.

    Args:
        error_code (str): The error code.
        **kwargs: Any additional context data to be interpolated in the error message.

    Returns:
        str: The constructed error message.
    """
    try:
        error_message = ERROR_CODES.get(error_code, ERROR_CODES["E3XXX"]).error_message.format(**kwargs)
    except KeyError as missing_kwarg:
        error_message = f"Error Code was found, but failed to format, message expected kwarg `{missing_kwarg}`."
    except Exception:  # pylint: disable=broad-except
        error_message = "Error Code was found, but failed to format message, unknown cause."
    return f"{error_code}: {error_message}"
