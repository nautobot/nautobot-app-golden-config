# v1.1 Release Notes

- Updates to filters and bug fixes

### Announcements

- Nautobot Golden Config `1.2.X` will remove scope as a JSON payload in GoldenConfigSetting to be replaced with DynamicGroups
- Nautobot Golden Config `1.2.X` will require Nautobot `v1.4.X` or greater

## v1.1.3 - 2022-08

### Fixed

- [#329](https://github.com/nautobot/nautobot-app-golden-config/issues/329) Change the pivot to use slug as name could have special characters that cause failures: Cherry picked

## v1.1.2 - 2022-08

### Changed

- [#322](https://github.com/nautobot/nautobot-app-golden-config/issues/322) Create release v1.1.2 and remove restrictions enforcing non-usage of beyond Nautobot 1.3.

## v1.1.1 - 2022-08

### Fixed

- [#260](https://github.com/nautobot/nautobot-app-golden-config/issues/260) Server Error when viewing Compliance Report <Overview>: Cherry picked
- [#309](https://github.com/nautobot/nautobot-app-golden-config/issues/309) Fix duplicate entries on home view:  Cherry picked

## v1.1.0 - 2022-06

### Fixed

- [#281](https://github.com/nautobot/nautobot-app-golden-config/issues/281) Fixes Views for Nautobot 1.3 Settings, backwards compatible with Nautobot 1.2
- [#270](https://github.com/nautobot/nautobot-app-golden-config/issues/270) Optimize GoldenConfig home view to improve scaling with > 1 GoldenConfigSetting via query annotations

### Added

- [#267](https://github.com/nautobot/nautobot-app-golden-config/issues/267) Add filterset to the GoldenConfigSettingViewSet
- [#262](https://github.com/nautobot/nautobot-app-golden-config/issues/262) Add filter for slug on ComplianceFeature
