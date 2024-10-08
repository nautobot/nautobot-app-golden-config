
# v2.1 Release Notes

- Added support for XML Compliance.
- Hide Compliance tab if no compliance result exists.


## v2.1.2 2024-08

### Fixed

- [#792](https://github.com/nautobot/nautobot-app-golden-config/issues/792) - Fixed issue with dynamic groups not being called in 2.3.0.
- [#800](https://github.com/nautobot/nautobot-app-golden-config/issues/800) - Fixed issue where compliance amongst other fields were not being updated when Django 4.2 was installed.

### Changed

- [#792](https://github.com/nautobot/nautobot-app-golden-config/issues/792) - Added an experimental `_manual_dynamic_group_mgmt` config to collect feedback on appropriate methodology, use at your own risk!!.

### Housekeeping

- [#786](https://github.com/nautobot/nautobot-app-golden-config/issues/786) - Fixed incorrect test data setup for `test_tags_filter()` test for `ConfigPlanFilterTestCase`.
- [#788](https://github.com/nautobot/nautobot-app-golden-config/issues/788) - Rebaked from the cookie `nautobot-app-v2.3.0`.

## v2.1.1 - 2024-07

### Fixed

- [#773](https://github.com/nautobot/nautobot-app-golden-config/issues/773) - Fixed deepdiff dependency range.

### Dependencies

- [#769](https://github.com/nautobot/nautobot-app-golden-config/issues/769) - Updated django-pivot to ~1.9.0.

### Documentation

- [#771](https://github.com/nautobot/nautobot-app-golden-config/issues/771) - Updated navigation tree for documentation updates for 2.1 release notes and XML compliance.
- [#775](https://github.com/nautobot/nautobot-app-golden-config/issues/775) - Add FAQ for deepdiff and numpy dependency issue.
- [#776](https://github.com/nautobot/nautobot-app-golden-config/issues/776) - Updated app config and urls config for providing link to documentation.

### Housekeeping

- [#769](https://github.com/nautobot/nautobot-app-golden-config/issues/769) - Added view tests for ConfigComplianceUIViewSet.


## v2.1.0 - 2024-05

### Added

- [#708](https://github.com/nautobot/nautobot-app-golden-config/issues/708) - Add Support for XML Compliance

### Fixed

- [#723](https://github.com/nautobot/nautobot-app-golden-config/issues/723) - Hide compliance tab in device view if no compliance results exist.
