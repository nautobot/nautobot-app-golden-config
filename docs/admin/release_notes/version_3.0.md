

## [v3.0.2 (2026-01-30)](https://github.com/nautobot/nautobot-app-golden-config/releases/tag/v3.0.2)

### Changed

- [#1073](https://github.com/nautobot/nautobot-app-golden-config/issues/1073) - Changed Compliance Rule's "Config to Match" form field to preserve leading spaces to properly match some operating systems.

### Dependencies

- Updated the minimum version of netutils to 1.17.0.
- Updated the minimum version of hier-config to 3.4.1.

# v3.0 Release Notes

This document describes all new features and changes in the release. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Release Overview

This major release marks the compatibility of the Nautobot Plugin Golden Config App with Nautobot 3.0.0. Check out the [full details](https://docs.nautobot.com/projects/core/en/stable/release-notes/version-3.0/) of the changes included in this new major release of Nautobot. Highlights:

- Minimum Nautobot version supported is 3.0.
- Added support for Python 3.13 and removed support for 3.9.
- Updated UI framework to use latest Bootstrap 5.3.
- Changed the charts rendering engine to Apache ECharts.

We will continue to support the previous major release for users of Nautobot LTM 2.4 only with critical bug and security fixes as per the [Software Lifecycle Policy](https://networktocode.com/company/legal/software-lifecycle-policy/).

## [v3.0.1 (2026-01-22)](https://github.com/nautobot/nautobot-app-golden-config/releases/tag/v3.0.1)

### Fixed

- [#1011](https://github.com/nautobot/nautobot-app-golden-config/issues/1011) - Fixed FAQ for remediation.
- [#1030](https://github.com/nautobot/nautobot-app-golden-config/issues/1030) - Fixed a bug with Config Plans being deployed despite the cancel button being clicked.
- [#1041](https://github.com/nautobot/nautobot-app-golden-config/issues/1041) - Fixed compliance filter buttons appearance.
- [#1050](https://github.com/nautobot/nautobot-app-golden-config/issues/1050) - Added Data Compliance tab on a Golden Config view.
- [#1051](https://github.com/nautobot/nautobot-app-golden-config/issues/1051) - Improved gc_repo_prep decorator compatibility with Inherited Jobs.
- [#1055](https://github.com/nautobot/nautobot-app-golden-config/issues/1055) - Fixed permissions for the GC Compliance report view.
- [#1061](https://github.com/nautobot/nautobot-app-golden-config/issues/1061) - Fixed an issue where Hier Config Remediation Options were not being applied.

### Documentation

- [#1035](https://github.com/nautobot/nautobot-app-golden-config/issues/1035) - Added Demo Instance Methodology section to Intended Configuration documentation showing how the demo instance configures Golden Config settings.
- [#1045](https://github.com/nautobot/nautobot-app-golden-config/issues/1045) - Updated documentation removing old references and updated a few images with dark mode.
- [#1062](https://github.com/nautobot/nautobot-app-golden-config/issues/1062) - Updated documentation to include 3.0 screenshots.
- Sync in LTM release notes into main app documentation.

### Housekeeping

- Rebaked from the cookie `nautobot-app-v3.0.0`.

## [v3.0.0 (2025-11-17)](https://github.com/nautobot/nautobot-app-golden-config/releases/tag/v3.0.0)

### Added

- Added support for Python 3.13.
- Added support for Nautobot 3.0.

### Changed

- [#1016](https://github.com/nautobot/nautobot-app-golden-config/issues/1016) - Changed the rendering engine from mat_plot_lib to Apache ECharts.
- [#1016](https://github.com/nautobot/nautobot-app-golden-config/issues/1016) - Updated imports to use preferred `nautobot.apps.*` where applicable.
- [#1016](https://github.com/nautobot/nautobot-app-golden-config/issues/1016) - Updated compliance view to use collapsible cards.
- [#1016](https://github.com/nautobot/nautobot-app-golden-config/issues/1016) - Updated navigation icon.

### Fixed

- [#1016](https://github.com/nautobot/nautobot-app-golden-config/issues/1016) - Fixed imports that are no longer supported.
- [#1016](https://github.com/nautobot/nautobot-app-golden-config/issues/1016) - Fixed DJLint errors.
- [#1031](https://github.com/nautobot/nautobot-app-golden-config/issues/1031) - Fixed various issues with templates and modals.
- [#1034](https://github.com/nautobot/nautobot-app-golden-config/issues/1034) - Fixed Javascript failing to load in Config Plan Post Processing.
- [#1031](https://github.com/nautobot/nautobot-app-golden-config/issues/1031) - Fixed various issues with templates and modals.

### Dependencies

- [#1016](https://github.com/nautobot/nautobot-app-golden-config/issues/1016) - Removed `mat_plot_lib` as a dependency.

### Housekeeping

- [#2109](https://github.com/nautobot/nautobot-app-golden-config/issues/2109) - Replaced deprecated object_edit template.

### Removed

- Dropped support for Python 3.9.

## [v3.0.0a4 (2025-11-05)](https://github.com/nautobot/nautobot-app-golden-config/releases/tag/v3.0.0a4)

## [v3.0.0a3 (2025-11-04)](https://github.com/nautobot/nautobot-app-golden-config/releases/tag/v3.0.0a3)

## [v3.0.0a1 (2025-10-31)](https://github.com/nautobot/nautobot-app-golden-config/releases/tag/v3.0.0a1)

