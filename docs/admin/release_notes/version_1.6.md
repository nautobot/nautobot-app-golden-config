# v1.6 Release Notes

- Add ability to generate ConfigPlans for configurations that need to be deployed, based on multiple plan types.
- Add a job that can deploy config_set based on a generated ConfigPlan object.
- Add functionality to compliance result to provide a Remediation plan.
- Supports Nautobot >=1.6.1,<2.0.0.

## v1.6.1 - 2023-09

### Changed

- [#600](https://github.com/nautobot/nautobot-plugin-golden-config/pull/600) - Updated readme to include the additional use cases covered.

### Fixed

- [#603](https://github.com/nautobot/nautobot-plugin-golden-config/pull/603) - Fix missing fields from the "AllDevicesGoldenConfig" Job.
- [#609](https://github.com/nautobot/nautobot-plugin-golden-config/pull/609) - Fixed issue where not all jinja filers, specifically netutils were being loaded into Jinja environment.
- [#609](https://github.com/nautobot/nautobot-plugin-golden-config/pull/609) - Fixed issues if a Job was never created since the feature was disabled, it would cause a stacktrace.
- [#609](https://github.com/nautobot/nautobot-plugin-golden-config/pull/609) - Fixed issue where in GoldenConfigSetting page, dynamic group selection would not show all of the eligible options.
- [#609](https://github.com/nautobot/nautobot-plugin-golden-config/pull/609) - Fixed issue where you could not fill in `jinja_env['undefined']` vars as a string, only a complex class.
- [#609](https://github.com/nautobot/nautobot-plugin-golden-config/pull/609) - Added the ability to generate remediation configurations and store in ConfigRemediation model

## v1.6.0 - 2023-09

### Added

- [#573](https://github.com/nautobot/nautobot-plugin-golden-config/pull/573) - Added the ability to generate remediation configurations and store in ConfigRemediation model
- [#573](https://github.com/nautobot/nautobot-plugin-golden-config/pull/573) - Added the ability to generate configurations that you plan to deploy from a variety of methods, such as Remediation, intended, manual, etc. via the ConfigPlan model.
- [#573](https://github.com/nautobot/nautobot-plugin-golden-config/pull/573) - Added the ability to Deploy configurations from the ConfigPlan configurations to your network devices.
- [#578](https://github.com/nautobot/nautobot-plugin-golden-config/pull/578) - Updated ComplianceRule and ComplianceRule forms to include tags.

### Fixed

- [#585](https://github.com/nautobot/nautobot-plugin-golden-config/pull/585) - Remove Jquery dependency from Google APIs, inherit from Nautobot core instead.
- [#577](https://github.com/nautobot/nautobot-plugin-golden-config/pull/577) - Fixed various forms fields and filters fields.
- [#577](https://github.com/nautobot/nautobot-plugin-golden-config/pull/577) - Updated default has_sensitive_data boolean to False.
- [#577](https://github.com/nautobot/nautobot-plugin-golden-config/pull/577) - Added warning message on views when required jobs are not enabled.
