# v1.2 Release Notes
- Move GoldenConfigSetting scope to the use of DynamicGroups
- Drop support of Nautobot <1.4.X

## v1.2.0b1 - 2022-08

### Changed

- #288 DynamicGroup Support
- #288 Updated invoke tasks to current standards
- #288 Initial changes for CI to work with latest pattern
- #288 GoldenConfigSetting.scope is not a property that maps to GoldenConfigSetting.dynamic_group.filter
- #288 GoldenConfigSetting.scope now has a setter method to create a DynamicGroup
  - Scope of Device objects can only be updated via the DynamicGroup is using the UI
  - The setter is for backwards compantibility for existing automation against the API

### Removed

- #288 Nautobot <1.4.0 support
