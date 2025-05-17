# v1.6 Release Notes

- Add ability to generate ConfigPlans for configurations that need to be deployed, based on multiple plan types.
- Add a job that can deploy config_set based on a generated ConfigPlan object.
- Add functionality to compliance result to provide a Remediation plan.
- Supports Nautobot >=1.6.1,<2.0.0.

## v1.6.6 - 2024-08

### Fixed

- [#787](https://github.com/nautobot/nautobot-app-golden-config/pull/787) - Allow version 7 of deepdiff.

## v1.6.5 - 2024-04

### Fixed

- [#714](https://github.com/nautobot/nautobot-app-golden-config/pull/714) - Fixed close threaded db connections during config deployment.
- [#744](https://github.com/nautobot/nautobot-app-golden-config/pull/744) - Fixed issue where parser is not mapped when not matching netutils normalized names.

### Changed

- [#744](https://github.com/nautobot/nautobot-app-golden-config/pull/744) - Changed netutils to support 1.8.0 and up.

## v1.6.4 - 2024-01

### Fixed

- [#695](https://github.com/nautobot/nautobot-app-golden-config/pull/695) - Removed optional job_result parameter from ensure_git_repository.

### Changed

- [#670](https://github.com/nautobot/nautobot-app-golden-config/pull/670) - Update Nautobot Nornir Dependency.

## v1.6.3 - 2023-10

### Fixed

- [#668](https://github.com/nautobot/nautobot-app-golden-config/issue/668) - Removed unneeded lookup for GoldenConfigSetting

## v1.6.2 - 2023-09

### Fixed

- [#621](https://github.com/nautobot/nautobot-app-golden-config/pull/621) - Moved jinja to be locally scoped, this was causing issues with Jinja filters based on import order.

## v1.6.1 - 2023-09

### Changed

- [#600](https://github.com/nautobot/nautobot-app-golden-config/pull/600) - Updated readme to include the additional use cases covered.

### Fixed

- [#603](https://github.com/nautobot/nautobot-app-golden-config/pull/603) - Fix missing fields from the "AllDevicesGoldenConfig" Job.
- [#609](https://github.com/nautobot/nautobot-app-golden-config/pull/609) - Fixed issue where not all jinja filers, specifically netutils were being loaded into Jinja environment.
- [#609](https://github.com/nautobot/nautobot-app-golden-config/pull/609) - Fixed issues if a Job was never created since the feature was disabled, it would cause a stacktrace.
- [#609](https://github.com/nautobot/nautobot-app-golden-config/pull/609) - Fixed issue where in GoldenConfigSetting page, dynamic group selection would not show all of the eligible options.
- [#609](https://github.com/nautobot/nautobot-app-golden-config/pull/609) - Fixed issue where you could not fill in `jinja_env['undefined']` vars as a string, only a complex class.
- [#609](https://github.com/nautobot/nautobot-app-golden-config/pull/609) - Added the ability to generate remediation configurations and store in ConfigRemediation model

## v1.6.0 - 2023-09

### Added

- [#573](https://github.com/nautobot/nautobot-app-golden-config/pull/573) - Added the ability to generate remediation configurations and store in ConfigRemediation model
- [#573](https://github.com/nautobot/nautobot-app-golden-config/pull/573) - Added the ability to generate configurations that you plan to deploy from a variety of methods, such as Remediation, intended, manual, etc. via the ConfigPlan model.
- [#573](https://github.com/nautobot/nautobot-app-golden-config/pull/573) - Added the ability to Deploy configurations from the ConfigPlan configurations to your network devices.
- [#578](https://github.com/nautobot/nautobot-app-golden-config/pull/578) - Updated ComplianceRule and ComplianceRule forms to include tags.

### Fixed

- [#585](https://github.com/nautobot/nautobot-app-golden-config/pull/585) - Remove Jquery dependency from Google APIs, inherit from Nautobot core instead.
- [#577](https://github.com/nautobot/nautobot-app-golden-config/pull/577) - Fixed various forms fields and filters fields.
- [#577](https://github.com/nautobot/nautobot-app-golden-config/pull/577) - Updated default has_sensitive_data boolean to False.
- [#577](https://github.com/nautobot/nautobot-app-golden-config/pull/577) - Added warning message on views when required jobs are not enabled.
