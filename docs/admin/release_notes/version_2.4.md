
# v2.4 Release Notes

This document describes all new features and changes in the release. The format is based on [Keep a
Changelog](https://keepachangelog.com/en/1.0.0/) and this project adheres to [Semantic
Versioning](https://semver.org/spec/v2.0.0.html).

## Release Overview

- Major features or milestones
- Changes to compatibility with Nautobot and/or other apps, libraries etc.

## [v2.4.0 (2025-02-20)](https://github.com/nautobot/nautobot-app-golden-config/releases/tag/v2.4.0)

### Added

- [#875](https://github.com/nautobot/nautobot-app-golden-config/issues/875) - Added Config Plan Post Processing to Config plan detail view.
- [#875](https://github.com/nautobot/nautobot-app-golden-config/issues/875) - Added Config plan post processing to configuration deployment stage.
- [#875](https://github.com/nautobot/nautobot-app-golden-config/issues/875) - Drop Python 3.8 support.

### Changed

- [#866](https://github.com/nautobot/nautobot-app-golden-config/issues/866) - Changed compliance_feature, compliance_rule, config_remove, config_replace, and config_remediation detail views to new component UI.
- [#866](https://github.com/nautobot/nautobot-app-golden-config/issues/866) - Changed the supported Nautobot to 2.4.2.

### Fixed

- [#706](https://github.com/nautobot/nautobot-app-golden-config/issues/706) - Fixed filtering when using a dynamic group of groups
- [#781](https://github.com/nautobot/nautobot-app-golden-config/issues/781) - Fixed UniqueViolation error when applying migration 0029 with multiple config plans sharing same device, date and plan_type.
- [#846](https://github.com/nautobot/nautobot-app-golden-config/issues/846) - - Fixed missing provides content check for GC settings syncing from Git Repo.
- [#863](https://github.com/nautobot/nautobot-app-golden-config/issues/863) - Updated the queryset altering to be after permissions restriction for config compliance list view.
- [#863](https://github.com/nautobot/nautobot-app-golden-config/issues/863) - Updated the queryset before rendering the compliance reporting to be after permissions restriction.

### Housekeeping

- [#809](https://github.com/nautobot/nautobot-app-golden-config/issues/809) - Added management command `generate_app_test_data` to generate sample data for development environments.
- [#890](https://github.com/nautobot/nautobot-app-golden-config/issues/890) - Added upper bound for Nautobot version so that Nautobot does not get upgraded automatically to an unsupported version.
