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
        troubleshooting="Open the Approval Workflow Definition referenced by the Golden Config Setting and check that it has at least one stage.",
        description="A Config Plan was generated for a device whose Golden Config Setting names an Approval Workflow Definition that cannot be started, so the Config Plan was not created.",
        error_message="Cannot start approval workflow `{definition}` for the config plan on `{device}`, the definition has no stages.",
        recommendation="Add an approval stage to the Approval Workflow Definition, or remove it from the Golden Config Setting.",
    ),
    "E3035": ErrorCode(
        troubleshooting="Check the approval state and status of the Config Plan.",
        description="A Config Plan can only be resubmitted when its approval workflow was denied or canceled and its deployment has not started.",
        error_message="Cannot resubmit `{config_plan}` for approval: {reason}.",
        recommendation="Generate a new Config Plan if the approval workflow definition was deleted or the deployment has already started.",
    ),
}
