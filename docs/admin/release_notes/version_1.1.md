# v1.1 Release Notes
- Updates to filters and bug fixes

## v1.1.0 - 2022-06

### Announcements

- Nautobot Golden Config 2.X.X will remove scope as a JSON payload in GoldenConfigSetting to be replaced with DynamicGroups
- Nautobot Golden Config 2.X.X will require Nautobot v1.3.X or greater

### Fixed

- #281 Fixes Views for Nautobot 1.3 Settings, backwards compatible with Nautobot 1.2
- #270 Optimize GoldenConfig home view to improve scaling with > 1 GoldenConfigSetting via query annotations

### Added

- #267 Add filterset to the GoldenConfigSettingViewSet
- #262 Add filter for slug on ComplianceFeature
