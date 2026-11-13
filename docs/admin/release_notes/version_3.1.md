# v3.1 Release Notes

This document describes all new features and changes in the release. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Release Overview

This minor release adds tag support across all Golden Config models and a bulk edit view for Golden Config records, along with a set of reliability fixes for jobs and compliance.

<!-- towncrier release notes start -->

## [v3.1.0 (2026-11-13)](https://github.com/nautobot/nautobot-app-golden-config/releases/tag/v3.1.0)

### Added

- [#1121](https://github.com/nautobot/nautobot-app-golden-config/issues/1121) - Added support for syncing tags onto Golden Config properties via the Git datasource YAML files.
- Added a bulk edit view for Golden Config (Configuration Overview) records.
- Added tag support throughout the UI for all Golden Config models: tags can be added and removed in bulk edit, filtered on from every list view, and displayed as an optional table column.

### Fixed

- [#677](https://github.com/nautobot/nautobot-app-golden-config/issues/677) - Fixed the drf_spectacular type hint warning for `ConfigToPushSerializer.get_config` at startup.
- [#766](https://github.com/nautobot/nautobot-app-golden-config/issues/766) - Fixed `MultipleObjectsReturned` in the post-migrate signal when another app has a Job class named `DeployConfigPlanJobButtonReceiver`.
- [#778](https://github.com/nautobot/nautobot-app-golden-config/issues/778) - Added validation to reject Golden Config Setting path templates that start with `/`.
- [#960](https://github.com/nautobot/nautobot-app-golden-config/issues/960) - Fixed `FieldError` when sorting the Config Overview table by device name.
- [#1020](https://github.com/nautobot/nautobot-app-golden-config/issues/1020) - Added support for unordered XML element comparison in compliance checks when config_ordered=False.
- [#1128](https://github.com/nautobot/nautobot-app-golden-config/issues/1128) - Fixed unexpected job exceptions, such as a soft time limit, being discarded without a log entry when `fail_job_on_task_failure` is unchecked.
- [#1160](https://github.com/nautobot/nautobot-app-golden-config/issues/1160) - Fixed debug log messages no longer being recorded in Golden Config job results when the debug option was not enabled. This has the potential to break any automation that previously relied on the presence of these log messages, so you may need to update your scheduled jobs to ensure they are run with the debug option enabled.
- [#1160](https://github.com/nautobot/nautobot-app-golden-config/issues/1160) - Changed Nornir play log entries without a grouping to use the `main` grouping.
- Fixed the Config Compliance device tab returning a server error instead of a 404 when the requested device does not exist.

### Dependencies

- [#1160](https://github.com/nautobot/nautobot-app-golden-config/issues/1160) - Changed the minimum version of nautobot-plugin-nornir to 3.4.0.

### Housekeeping

- [#1010](https://github.com/nautobot/nautobot-app-golden-config/issues/1010) - Removed commented-out Config Overview table header tests.
- [#1167](https://github.com/nautobot/nautobot-app-golden-config/issues/1167) - Updating CODEOWNERS
- Fixed unit tests that hardcoded the `/opt/nautobot/git` path to use `settings.GIT_ROOT`, for compatibility with the isolated test environment in newer Nautobot versions.
