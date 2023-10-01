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

## v2.0.0 - 2023-09

### Changed

- [#575](https://github.com/nautobot/nautobot-plugin-golden-config/pull/575) - Updated `nautobot` to `2.0.0` and made associated changes.
- [#575](https://github.com/nautobot/nautobot-plugin-golden-config/pull/575) - Changed dispatcher_mapping to custom_dispatcher and constance settings.
- [#575](https://github.com/nautobot/nautobot-plugin-golden-config/pull/575) - Changed Config Compliance view to be based on model, not dynamic group and provide a `message` when they have drifted.
- [#575](https://github.com/nautobot/nautobot-plugin-golden-config/pull/575) - Changed the location of the config compliance view to be a tab on device objects.
- [#575](https://github.com/nautobot/nautobot-plugin-golden-config/pull/575) - Changed the linking on Configuration Overview to point to the detailed object to align with Nautobot standards.
- [#575](https://github.com/nautobot/nautobot-plugin-golden-config/pull/575) - Inverted Config Plan logic to not show Completed Config Plans by default and have a button to see them.
- [#575](https://github.com/nautobot/nautobot-plugin-golden-config/pull/575) - Change logic to always include jobs, regardless of which features are in use.
- [#575](https://github.com/nautobot/nautobot-plugin-golden-config/pull/575) - Changed several of the URL locations of views, based on migration to viewsets and overall simplification of code.
- [#575](https://github.com/nautobot/nautobot-plugin-golden-config/pull/575) - Changed models to better reflect actual state, such as not to allow nullable on characters and one-to-one from config compliance to device model.
- [#575](https://github.com/nautobot/nautobot-plugin-golden-config/pull/575) - Changed any date/time reference to be django's `make_aware`.
- [#575](https://github.com/nautobot/nautobot-plugin-golden-config/pull/575) - Changed Nornir Processor logic on failures to be recursive lookups.
- [#575](https://github.com/nautobot/nautobot-plugin-golden-config/pull/575) - Updated diff2html to 3.4.43.
- [#575](https://github.com/nautobot/nautobot-plugin-golden-config/pull/575) - Changed booleans to be consistent with Nautobot UI.
- [#575](https://github.com/nautobot/nautobot-plugin-golden-config/pull/575) - Pinned django-pivot to 1.8.1 as that returns a  queryset.
- [#575](https://github.com/nautobot/nautobot-plugin-golden-config/pull/575) - Various cleanup updates such as moving to viewsets, hyperlinked_text, moving matplot code, using Nautobot provided Git capabilities, updating development environment to NTC standards, etc.

### Added

- [#575](https://github.com/nautobot/nautobot-plugin-golden-config/pull/575) - Introduced constance settings for DEFAULT_FRAMEWORK, GET_CONFIG_FRAMEWORK, MERGE_CONFIG_FRAMEWORK, and REPLACE_CONFIG_FRAMEWORK.
- [#575](https://github.com/nautobot/nautobot-plugin-golden-config/pull/575) - Added error code framework.
- [#575](https://github.com/nautobot/nautobot-plugin-golden-config/pull/575) - Added a setting for default_deploy_status to allow that to be configurable.
- [#575](https://github.com/nautobot/nautobot-plugin-golden-config/pull/575) - Added a job to sync dynamic group and config compliance model.
- [#575](https://github.com/nautobot/nautobot-plugin-golden-config/pull/575) - Added a custom logger capability to be able to handle stdout as well as nautobot job logs.
- [#575](https://github.com/nautobot/nautobot-plugin-golden-config/pull/575) - Added copy buttons in several locations to allow for getting configurations easier.
- [#575](https://github.com/nautobot/nautobot-plugin-golden-config/pull/575) - Added datasources yaml key to use network_driver but still backwards compatible to _slug.

### Removed

- [#575](https://github.com/nautobot/nautobot-plugin-golden-config/pull/575) - Remove the already deprecated "Scope" in favor of dynamic groups.
- [#575](https://github.com/nautobot/nautobot-plugin-golden-config/pull/575) - Removed references to git repository tokens.
- [#575](https://github.com/nautobot/nautobot-plugin-golden-config/pull/575) - Removed management command to run jobs in favor of Nautobot Core's usage.
- [#575](https://github.com/nautobot/nautobot-plugin-golden-config/pull/575) - Removed platform_slug_map in favor of constance settings.