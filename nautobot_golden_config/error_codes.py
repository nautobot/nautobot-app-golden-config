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
}
