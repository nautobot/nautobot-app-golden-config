# v1.2 Release Notes

- Move GoldenConfigSetting scope to the use of DynamicGroups
- Drop support of Nautobot <1.4.X
- Update docs to mkdocs and read the docs hosting

## v1.2.2 - 2022-10

### Fixed

- [#369](https://github.com/nautobot/nautobot-plugin-golden-config/issues/369) Using of runner plugin serial is causing an "InterfaceError: connection already closed" error.

### Changed

- [#367](https://github.com/nautobot/nautobot-plugin-golden-config/pull/367) Add suggested custom CSS for mkdocstrings indentation.

## v1.2.1 - 2022-10

### Fixed

- [#350](https://github.com/nautobot/nautobot-plugin-golden-config/pull/350) Fix lingering ssh connections by adding a close_connections in completed stage of processor.
- [#317](https://github.com/nautobot/nautobot-plugin-golden-config/issues/317) Fix The CI builds the Nautobot container two times in the unittests step.
- [#307](https://github.com/nautobot/nautobot-plugin-golden-config/issues/307) Fix `Bulk Delete` not always working on config compliance objects.
- [#358](https://github.com/nautobot/nautobot-plugin-golden-config/pull/358) Fix code block formatting in app_getting_started.md.
- [#352](https://github.com/nautobot/nautobot-plugin-golden-config/pull/352) Fix clearing DB connections between threads.

### Changed

- [#361](https://github.com/nautobot/nautobot-plugin-golden-config/pull/361) Adds environment variable to disable git prompts.
- [#362](https://github.com/nautobot/nautobot-plugin-golden-config/pull/362) Optimizing refreshing of repos when running jobs.

## v1.2.0 - 2022-08

### Changed

- [#323](https://github.com/nautobot/nautobot-plugin-golden-config/pull/323) Disable enforcement of `max_version` check and update admin install policy to indicate the same.
- [#321](https://github.com/nautobot/nautobot-plugin-golden-config/pull/321) Change source class to align with nautobot v1.4.0.
- [#324](https://github.com/nautobot/nautobot-plugin-golden-config/pull/324) Performance enhancements for dynamic groups.
- [#325](https://github.com/nautobot/nautobot-plugin-golden-config/pull/325) Doc updates.

### Fixed

- [#314](https://github.com/nautobot/nautobot-plugin-golden-config/issues/314) Fixed Tag filtering not working in job launch form
- [#316](https://github.com/nautobot/nautobot-plugin-golden-config/pull/316) & [#313](https://github.com/nautobot/nautobot-plugin-golden-config/pull/313) Update doc links for new read the docs
- [#306](https://github.com/nautobot/nautobot-plugin-golden-config/pull/306) Fix ability to run docs locally
- [#304](https://github.com/nautobot/nautobot-plugin-golden-config/pull/304) & [#305](https://github.com/nautobot/nautobot-plugin-golden-config/pull/305) Fix yaml line issues
- [#321](https://github.com/nautobot/nautobot-plugin-golden-config/pull/321) Resolving deprecation warning from upgrading to Nautobot v1.4.0.
- [#324](https://github.com/nautobot/nautobot-plugin-golden-config/pull/324) Provide performance enhancements to querying DynamicGroup members.
- [#328](https://github.com/nautobot/nautobot-plugin-golden-config/pull/328) Update container to be variable rather than hard code to py3.7.
- [#327](https://github.com/nautobot/nautobot-plugin-golden-config/pull/327) Change the pivot to use slug as name could have special characters that cause failures
- [#323](https://github.com/nautobot/nautobot-plugin-golden-config/pull/323) Convert to slug to match view

## v1.2.0b1 - 2022-08

### Added

- [#291](https://github.com/nautobot/nautobot-plugin-golden-config/pull/291) Updated codeowners

### Changed

- [#288](https://github.com/nautobot/nautobot-plugin-golden-config/issues/288) DynamicGroup Support
- [#288](https://github.com/nautobot/nautobot-plugin-golden-config/issues/288) Updated invoke tasks to current standards
- [#288](https://github.com/nautobot/nautobot-plugin-golden-config/issues/288) Initial changes for CI to work with latest pattern
- [#288](https://github.com/nautobot/nautobot-plugin-golden-config/issues/288) GoldenConfigSetting.scope is not a property that maps to GoldenConfigSetting.dynamic_group.filter
- [#288](https://github.com/nautobot/nautobot-plugin-golden-config/issues/288) GoldenConfigSetting.scope now has a setter method to create a DynamicGroup
    - Scope of Device objects can only be updated via the DynamicGroup is using the UI
    - The setter is for backwards compantibility for existing automation against the API
- [#280](https://github.com/nautobot/nautobot-plugin-golden-config/issues/280) Updated docs in preperation for doc centralization process
- [#289](https://github.com/nautobot/nautobot-plugin-golden-config/issues/289) Update Environment setup to NTC Standards
- [#287](https://github.com/nautobot/nautobot-plugin-golden-config/issues/287) Updated copy button to use Nautobot's standard copy functionality rather than one off

### Fixed

- [#260](https://github.com/nautobot/nautobot-plugin-golden-config/issues/260) Fixed issue with Compliance Report when values were None
- [#299](https://github.com/nautobot/nautobot-plugin-golden-config/issues/299) Updated Readme images to render properly on PyPi, fixed other links

### Removed

- [#288](https://github.com/nautobot/nautobot-plugin-golden-config/issues/288) Nautobot <1.4.0 support
