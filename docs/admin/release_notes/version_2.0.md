# v2.0 Release Notes

- Updated `nautobot` to `2.0.0` and made associated changes.
- Integrated all relevant sections with `Platform.network_driver`.
- Added a standard way to provide error codes.
- Changed Config Compliance view to be based on model, not dynamic group and provide a `message` when they have drifted.
- Added constance settings (`DEFAULT_FRAMEWORK`, `GET_CONFIG_FRAMEWORK`, `MERGE_CONFIG_FRAMEWORK`, and `REPLACE_CONFIG_FRAMEWORK`) and customer_dispatcher to remove dispatcher_mapping.
- Moved config compliance view to be a tab within device instead of a dedicated page.
- Removed management command in favor of Nautobot Core's.

!!! note
    Please see [migrating guide](../migrating_to_v2.md) for details on migration.


## v2.0.4 2024-04

### Fixed

- [#749](https://github.com/nautobot/nautobot-app-golden-config/issues/749) - Corrected issue where consecutive Golden Config Jobs in All Golden Configs Job wouldn't execute if prior Job had an Exception raised.

### Housekeeping

- [#741](https://github.com/nautobot/nautobot-app-golden-config/issues/741) - Re-baked from the latest template.


## v2.0.3 2024-03

### Added

- [#736](https://github.com/nautobot/nautobot-app-golden-config/issues/736) - Add a boolean job parameter `fail_job_on_task_failure` which will determine whether a single task failure anywhere in the job-result should result in job-result status of failed vs successful.

### Fixed

- [#736](https://github.com/nautobot/nautobot-app-golden-config/issues/736) - Fixes repo push and commit not executing if a exception was raised on any task inside a job.

## v2.0.2 - 2024-03

### Added

- [#707](https://github.com/nautobot/nautobot-app-golden-config/pull/707) - Added autoformat invoke command.
- [#730](https://github.com/nautobot/nautobot-app-golden-config/pull/730) - Added app config schema generator and validator.

### Fixed

- [#699](https://github.com/nautobot/nautobot-app-golden-config/pull/699) - Fixed stale reference to platform_slug_map.
- [#719](https://github.com/nautobot/nautobot-app-golden-config/pull/719) - Fixed generate config plans Status filter.
- [#715](https://github.com/nautobot/nautobot-app-golden-config/pull/715) - Fixed close threaded db connections during config deployment.
- [#726](https://github.com/nautobot/nautobot-app-golden-config/pull/726) - Fixed objectchange log excludes for object_data_v2 data as well.
- [#718](https://github.com/nautobot/nautobot-app-golden-config/pull/718) - Fixed logic to handle jobs requiring approvals.
- [#724](https://github.com/nautobot/nautobot-app-golden-config/pull/724) - Fixed performance issue on UNIX file diff view.
- [#724](https://github.com/nautobot/nautobot-app-golden-config/pull/724) - Fixed non-working repos list creation and syncing.
- [#731](https://github.com/nautobot/nautobot-app-golden-config/pull/731) - Fixed missing right panel with config types.
- [#734](https://github.com/nautobot/nautobot-app-golden-config/pull/734) - Fixed incorrect netutils_parser lookup.

### Changed

- [#691](https://github.com/nautobot/nautobot-app-golden-config/pull/691) - Changed repo name and references to nautobot-app-golden-config.
- [#707](https://github.com/nautobot/nautobot-app-golden-config/pull/707) - Changed from pydocstyle to ruff.
- [#707](https://github.com/nautobot/nautobot-app-golden-config/pull/707) - Changed release notes to towncrier based.

## v2.0.1 - 2023-12

### Fixed

- [#676](https://github.com/nautobot/nautobot-app-golden-config/pull/676) - Fixes docs for running config plan job in 2.0.
- [#680](https://github.com/nautobot/nautobot-app-golden-config/pull/680) - Resolve RTD build issue.
- [#684](https://github.com/nautobot/nautobot-app-golden-config/pull/684) - Fix repo sync not executing on any task failure.
- [#685](https://github.com/nautobot/nautobot-app-golden-config/pull/685) - Cherry-pick #669 - Removed unneeded lookup for GoldenConfigSetting.
- [#686](https://github.com/nautobot/nautobot-app-golden-config/pull/686) - Fix incorrect permissions.


### Changed

- [#658](https://github.com/nautobot/nautobot-app-golden-config/pull/658) - Cookie updated by NetworkToCode Cookie Drift Manager Tool.
- [#671](https://github.com/nautobot/nautobot-app-golden-config/pull/671) - Finish Documentation Updates from Drift Manager.

## v2.0.0 - 2023-09

### Changed

- [#575](https://github.com/nautobot/nautobot-app-golden-config/pull/575) - Updated `nautobot` to `2.0.0` and made associated changes.
- [#575](https://github.com/nautobot/nautobot-app-golden-config/pull/575) - Changed dispatcher_mapping to custom_dispatcher and constance settings.
- [#575](https://github.com/nautobot/nautobot-app-golden-config/pull/575) - Changed Config Compliance view to be based on model, not dynamic group and provide a `message` when they have drifted.
- [#575](https://github.com/nautobot/nautobot-app-golden-config/pull/575) - Changed the location of the config compliance view to be a tab on device objects.
- [#575](https://github.com/nautobot/nautobot-app-golden-config/pull/575) - Changed the linking on Configuration Overview to point to the detailed object to align with Nautobot standards.
- [#575](https://github.com/nautobot/nautobot-app-golden-config/pull/575) - Inverted Config Plan logic to not show Completed Config Plans by default and have a button to see them.
- [#575](https://github.com/nautobot/nautobot-app-golden-config/pull/575) - Change logic to always include jobs, regardless of which features are in use.
- [#575](https://github.com/nautobot/nautobot-app-golden-config/pull/575) - Changed several of the URL locations of views, based on migration to viewsets and overall simplification of code.
- [#575](https://github.com/nautobot/nautobot-app-golden-config/pull/575) - Changed models to better reflect actual state, such as not to allow nullable on characters and one-to-one from config compliance to device model.
- [#575](https://github.com/nautobot/nautobot-app-golden-config/pull/575) - Changed any date/time reference to be django's `make_aware`.
- [#575](https://github.com/nautobot/nautobot-app-golden-config/pull/575) - Changed Nornir Processor logic on failures to be recursive lookups.
- [#575](https://github.com/nautobot/nautobot-app-golden-config/pull/575) - Updated diff2html to 3.4.43.
- [#575](https://github.com/nautobot/nautobot-app-golden-config/pull/575) - Changed booleans to be consistent with Nautobot UI.
- [#575](https://github.com/nautobot/nautobot-app-golden-config/pull/575) - Pinned django-pivot to 1.8.1 as that returns a  queryset.
- [#575](https://github.com/nautobot/nautobot-app-golden-config/pull/575) - Various cleanup updates such as moving to viewsets, hyperlinked_text, moving matplot code, using Nautobot provided Git capabilities, updating development environment to NTC standards, etc.

### Added

- [#575](https://github.com/nautobot/nautobot-app-golden-config/pull/575) - Introduced constance settings for DEFAULT_FRAMEWORK, GET_CONFIG_FRAMEWORK, MERGE_CONFIG_FRAMEWORK, and REPLACE_CONFIG_FRAMEWORK.
- [#575](https://github.com/nautobot/nautobot-app-golden-config/pull/575) - Added error code framework.
- [#575](https://github.com/nautobot/nautobot-app-golden-config/pull/575) - Added a setting for default_deploy_status to allow that to be configurable.
- [#575](https://github.com/nautobot/nautobot-app-golden-config/pull/575) - Added a job to sync dynamic group and config compliance model.
- [#575](https://github.com/nautobot/nautobot-app-golden-config/pull/575) - Added a custom logger capability to be able to handle stdout as well as nautobot job logs.
- [#575](https://github.com/nautobot/nautobot-app-golden-config/pull/575) - Added copy buttons in several locations to allow for getting configurations easier.
- [#575](https://github.com/nautobot/nautobot-app-golden-config/pull/575) - Added datasources yaml key to use network_driver but still backwards compatible to _slug.

### Removed

- [#575](https://github.com/nautobot/nautobot-app-golden-config/pull/575) - Remove the already deprecated "Scope" in favor of dynamic groups.
- [#575](https://github.com/nautobot/nautobot-app-golden-config/pull/575) - Removed references to git repository tokens.
- [#575](https://github.com/nautobot/nautobot-app-golden-config/pull/575) - Removed management command to run jobs in favor of Nautobot Core's usage.
- [#575](https://github.com/nautobot/nautobot-app-golden-config/pull/575) - Removed platform_slug_map in favor of constance settings.