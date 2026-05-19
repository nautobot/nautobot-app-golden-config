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
    "E3038": ErrorCode(
        troubleshooting="Open the named Golden Config Setting and confirm whether the matching `enable_<feature>` flag is intentionally off. If two or more Settings have overlapping scope, the one with the highest `weight` wins; lower-weighted Settings are ignored for this device.",
        description="The job did not run for this device because its highest-weighted Golden Config Setting has the corresponding `enable_<feature>` flag set to `False` — or, less commonly, the device is not in scope of any Setting at all.",
        error_message=(
            "Device {device_name} skipped for {feature} job — highest-weighted Golden Config Setting "
            "'{setting_name}' (weight {setting_weight}) has enable_{feature}=False. "
            "Alternate form when the device has no winning Setting: "
            "Device {device_name} skipped for {feature} job — no eligible Golden Config Setting."
        ),
        recommendation="Enable the corresponding `enable_<feature>` flag on the winning Golden Config Setting, or adjust Setting weights / Dynamic Group scope so a different Setting wins for this device.",
    ),
    "E3039": ErrorCode(
        troubleshooting="Either no devices were in scope of any Golden Config Setting, or every in-scope device was disabled on its winning Setting (each is named in a preceding E3038 entry).",
        description="Summary line fired once per feature when the job's filtered device set is empty. Suppressed when exactly one device was filtered (the single preceding E3038 already names it).",
        error_message=(
            "{feature_label} {label} skipped — all {skipped_count} in-scope devices have it disabled "
            "on their winning Setting (see E3038 entries above). "
            "Alternate form when no devices were in scope at all: "
            "{feature_label} {label} skipped — no devices in scope of any Golden Config Setting."
        ),
        recommendation="Either expand a Golden Config Setting's Dynamic Group to include the intended devices, or enable the corresponding `enable_<feature>` flag on the winning Setting(s) named by the preceding E3038 entries.",
    ),
}
