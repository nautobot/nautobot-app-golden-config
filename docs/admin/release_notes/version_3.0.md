# v3.0 Release Notes

This document describes all new features and changes in the release. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Release Overview

This major release marks the compatibility of the Nautobot Plugin Golden Config App with Nautobot 3.0.0. Check out the [full details](https://docs.nautobot.com/projects/core/en/stable/release-notes/version-3.0/) of the changes included in this new major release of Nautobot. Highlights:

- Minimum Nautobot version supported is 3.0.
- Added support for Python 3.13 and removed support for 3.9.
- Updated UI framework to use latest Bootstrap 5.3.
- Migrated to ECharts

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

- [#1008](https://github.com/nautobot/nautobot-app-golden-config/issues/1008) - Fixed Unittest failure for ConfigPlan allowed_number_of_tree_queries_per_view_type.
- [#1016](https://github.com/nautobot/nautobot-app-golden-config/issues/1016) - Fixed imports that are no longer supported.
- [#1016](https://github.com/nautobot/nautobot-app-golden-config/issues/1016) - Fixed DJLint errors.
- [#1031](https://github.com/nautobot/nautobot-app-golden-config/issues/1031) - Fixed various issues with templates and modals.
- [#1034](https://github.com/nautobot/nautobot-app-golden-config/issues/1034) - Fixed Javascript failing to load in Config Plan Post Processing.
- [#1031](https://github.com/nautobot/nautobot-app-golden-config/issues/1031) - Fixed various issues with templates and modals.

### Dependencies

- [#1016](https://github.com/nautobot/nautobot-app-golden-config/issues/1016) - Removed `mat_plot_lib` as a dependency.

### Housekeeping

- [#1022](https://github.com/nautobot/nautobot-app-golden-config/issues/1022) - Update any call to `get_extra_context` to call super of the method first.
- [#2109](https://github.com/nautobot/nautobot-app-golden-config/issues/2109) - Replaced deprecated object_edit template.

### Removed

- Dropped support for Python 3.9.

## [v3.0.0a4 (2025-11-05)](https://github.com/nautobot/nautobot-app-golden-config/releases/tag/v3.0.0a4)

## [v3.0.0a3 (2025-11-04)](https://github.com/nautobot/nautobot-app-golden-config/releases/tag/v3.0.0a3)

## [v3.0.0a1 (2025-10-31)](https://github.com/nautobot/nautobot-app-golden-config/releases/tag/v3.0.0a1)

