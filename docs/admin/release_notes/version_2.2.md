
# v2.2 Release Notes

This document describes all new features and changes in the release. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Release Overview

- Added Python 3.12 support.
- Added REST API endpoint for Jinja as first part of journey towards a jinja live editor.

## [v2.2.1 (2024-11-27)](https://github.com/nautobot/nautobot-app-golden-config/releases/tag/v2.2.1)

### Added

- [#827](https://github.com/nautobot/nautobot-app-golden-config/issues/827) - Added a web ui for Jinja template developers to render intended configurations.

### Fixed

- [#831](https://github.com/nautobot/nautobot-app-golden-config/issues/831) - Resolved issue with tests failing in Nautobot 2.3.11.
- [#835](https://github.com/nautobot/nautobot-app-golden-config/issues/835) - Resolved error when accessing the Golden Config Settings list view in Nautobot v2.3.11 and higher.

## [v2.2.0 (2024-11-04)](https://github.com/nautobot/nautobot-app-golden-config/releases/tag/v2.2.0)

### Added

- [#803](https://github.com/nautobot/nautobot-app-golden-config/issues/803) - Added Python 3.12 support.
- [#824](https://github.com/nautobot/nautobot-app-golden-config/issues/824) - Added a REST API endpoint for Jinja template developers to render intended configurations from templates in an arbitrary git repository.

### Changed

- [#814](https://github.com/nautobot/nautobot-app-golden-config/issues/814) - Changed the Git commit message of GC Jobs to be configurable.

### Fixed

- [#743](https://github.com/nautobot/nautobot-app-golden-config/issues/743) - Fixed improperly rendered panels in device and location views.
- [#810](https://github.com/nautobot/nautobot-app-golden-config/issues/810) - Fixed custom compliance to work with non-string objects.

### Housekeeping

- [#0](https://github.com/nautobot/nautobot-app-golden-config/issues/0) - Rebaked from the cookie `nautobot-app-v2.4.0`.
- [#803](https://github.com/nautobot/nautobot-app-golden-config/issues/803) - Rebaked from the cookie `nautobot-app-v2.3.2`.
- [#823](https://github.com/nautobot/nautobot-app-golden-config/issues/823) - Changed model_class_name in .cookiecutter.json to a valid model to help with drift management.
- [#824](https://github.com/nautobot/nautobot-app-golden-config/issues/824) - Updated multiple tests to use the faster `setUpTestData` instead of `setUp`. Fixed incorrect base class on `ConfigPlanTest`.
