# v3.0 Release Notes

This document describes all new features and changes in the release. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Release Overview

- Migrated to ECharts
- Added support for Nautobot 3.0.
- Added support for Python 3.13.
- Dropped support for Python 3.9.

## [v3.0.0a2 (2025-11-04)](https://github.com/nautobot/nautobot-app-golden-config/releases/tag/v3.0.0a2)

### Changed

- [#1016](https://github.com/nautobot/nautobot-app-golden-config/issues/1016) - Changed the rendering engine from mat_plot_lib to Apache ECharts.
- [#1016](https://github.com/nautobot/nautobot-app-golden-config/issues/1016) - Updated imports to use preferred `nautobot.apps.*` where applicable.
- [#1016](https://github.com/nautobot/nautobot-app-golden-config/issues/1016) - Updated compliance view to use collapsible cards.
- [#1016](https://github.com/nautobot/nautobot-app-golden-config/issues/1016) - Updated navigation icon.

### Fixed

- [#1016](https://github.com/nautobot/nautobot-app-golden-config/issues/1016) - Fixed imports that are no longer supported.
- [#1016](https://github.com/nautobot/nautobot-app-golden-config/issues/1016) - Fixed DJLint errors.

### Dependencies

- [#1016](https://github.com/nautobot/nautobot-app-golden-config/issues/1016) - Removed `mat_plot_lib` as a dependency.


## [v3.0.0a1 (2025-10-31)](https://github.com/nautobot/nautobot-app-golden-config/releases/tag/v3.0.0a1)

### Added

- Added support for Python 3.13.
- Added support for Nautobot 3.0.

### Removed

- Dropped support for Python 3.9.
