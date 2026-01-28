# v2.6 Release Notes

This document describes all new features and changes in the release. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Release Overview

- Changed minimum Nautobot version to 2.4.20.
- Dropped support for Python 3.9.

<!-- towncrier release notes start -->


## [v2.6.2 (2026-01-28)](https://github.com/nautobot/nautobot-app-golden-config/releases/tag/v2.6.2)

### Changed

- [#1073](https://github.com/nautobot/nautobot-app-golden-config/issues/1073) - Changed Compliance Rule's "Config to Match" form field to preserve leading spaces to properly match some operating systems.

### Fixed

- [#1053](https://github.com/nautobot/nautobot-app-golden-config/issues/1053) - Fixed various issues with templates and modals.
- [#1061](https://github.com/nautobot/nautobot-app-golden-config/issues/1061) - Fixed an issue where Hier Config Remediation Options were not being applied.

### Housekeeping

- [#1069](https://github.com/nautobot/nautobot-app-golden-config/issues/1069) - Updated django-debug-toolbar to 4.4.0 to fix import errors.

## [v2.6.1 (2025-12-16)](https://github.com/nautobot/nautobot-app-golden-config/releases/tag/v2.6.1)

### Fixed

- [#1051](https://github.com/nautobot/nautobot-app-golden-config/issues/1051) - Improved gc_repo_prep decorator compatibility with Inherited Jobs.

## [v2.6.0 (2025-12-05)](https://github.com/nautobot/nautobot-app-golden-config/releases/tag/v2.6.0)

### Housekeeping

- [#1008](https://github.com/nautobot/nautobot-app-golden-config/issues/1008) - Fixed Unittest failure for ConfigPlan allowed_number_of_tree_queries_per_view_type.
- [#1022](https://github.com/nautobot/nautobot-app-golden-config/issues/1022) - Update any call to `get_extra_context` to call super of the method first.
- Rebaked from the cookie `nautobot-app-v2.7.0`.
- Rebaked from the cookie `nautobot-app-v2.7.1`.
- Rebaked from the cookie `nautobot-app-v2.7.2`.
