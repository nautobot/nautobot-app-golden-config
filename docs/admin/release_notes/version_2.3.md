# v2.3 Release Notes

This document describes all new features and changes in the release. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Release Overview

- Added a `branch` parameter to the "Generate Intended Config" view.
- Fixed some bugs in the UI for device compliance and config compliance views.

## [v2.3.0 (2025-02-03)](https://github.com/nautobot/nautobot-app-golden-config/releases/tag/v2.3.0)

### Added

- [#828](https://github.com/nautobot/nautobot-app-golden-config/issues/828) - Added `branch` parameter to generate intended config view.

### Changed

- [#860](https://github.com/nautobot/nautobot-app-golden-config/issues/860) - Added a scroll bar and maximum height to the "Configuration" text boxes on the device configuration compliance tabs.

### Fixed

- [#812](https://github.com/nautobot/nautobot-app-golden-config/issues/812) - Fixed a bug in the config compliance list view when customizing the table columns.

### Housekeeping

- Rebaked from the cookie `nautobot-app-v2.4.1`.
- [#873](https://github.com/nautobot/nautobot-app-golden-config/issues/873) - Fixed failing tests in Nautobot v2.3.11 and higher.
- [#857](https://github.com/nautobot/nautobot-app-golden-config/issues/857) - Fixed installation docs to make clear that configurations are sample configurations.
