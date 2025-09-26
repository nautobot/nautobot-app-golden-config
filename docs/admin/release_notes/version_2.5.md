
# v2.5 Release Notes

This document describes all new features and changes in the release. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Release Overview

- Updated DeepDiff dependency to address CVE-2025-58367.
- Updated heir_config from v2 to v3.
- Add the ability to manage remediation settings via Git data sources.
- Add additional options to fail Config Plans better.

## [v2.5.1 (2025-09-26)](https://github.com/nautobot/nautobot-app-golden-config/releases/tag/v2.5.1)

### Changed

- [#994](https://github.com/nautobot/nautobot-app-golden-config/issues/994) - Increased Change Control URL field max length from 256 to 2048 characters in Config Plan model.

### Fixed

- [#994](https://github.com/nautobot/nautobot-app-golden-config/issues/994) - Fixed Change Control URL field max length in the Config Plan bulk edit form.
- [#995](https://github.com/nautobot/nautobot-app-golden-config/issues/995) - Fixed Compatibility Matrix by adding versions 2.4.x and 2.5.x.

### Housekeeping

- Rebaked from the cookie `nautobot-app-v2.6.0`.
- Updated ltm-1.6 release notes with new patch release information.

## [v2.5.0 (2025-09-09)](https://github.com/nautobot/nautobot-app-golden-config/releases/tag/v2.5.0)

### Security

- [#989](https://github.com/nautobot/nautobot-app-golden-config/issues/989) - Upgraded DeepDiff to `8.6.1` version to address CVE-2025-58367.

### Added

- [#870](https://github.com/nautobot/nautobot-app-golden-config/issues/870) - Added the ability to sync remediation settings from a Git repository.
- [#898](https://github.com/nautobot/nautobot-app-golden-config/issues/898) - Added tests to ensure that mkdocs release notes are properly set.
- [#921](https://github.com/nautobot/nautobot-app-golden-config/issues/921) - Added testing for the two issues with mkdocs versus markdown rendering and associated fixes.
- [#955](https://github.com/nautobot/nautobot-app-golden-config/issues/955) - Added an option to fail the Config Plan Deployment Job if any tasks for any device fails.

### Changed

- [#902](https://github.com/nautobot/nautobot-app-golden-config/issues/902) - Upgraded from hier_config v2.2.2 to v3.2.2, which is a breaking change from the hier_config side. The hier_config implementation was updated to reflect hier_config v3.
- Changed the Golden Config Setting form to use dynamic dropdowns for the related models.

### Fixed

- [#899](https://github.com/nautobot/nautobot-app-golden-config/issues/899) - Fixed template include errors during intended config rendering due to incorrect Jinja root path.
- [#940](https://github.com/nautobot/nautobot-app-golden-config/issues/940) - Implement a more performant ORM/DB query in-place of the existing for loop logic for device_to_settings_map.
- [#951](https://github.com/nautobot/nautobot-app-golden-config/issues/951) - Fixed potential duplicates in data migration by adding a check to validate time uniqueness.
- [#959](https://github.com/nautobot/nautobot-app-golden-config/issues/959) - Fix device_type filter for GC jobs.

### Documentation

- [#969](https://github.com/nautobot/nautobot-app-golden-config/issues/969) - Added Analytics GTM template override only to the public ReadTheDocs build.

### Housekeeping

- [#961](https://github.com/nautobot/nautobot-app-golden-config/issues/961) - Migrate Golden Config Setting, Config Plan, Golden Config models to UI Component Framework.
- [#970](https://github.com/nautobot/nautobot-app-golden-config/issues/970) - Regenerate lock file with poetry 1.8 version.
- Rebaked from the cookie `nautobot-app-v2.5.0`.
- Rebaked from the cookie `nautobot-app-v2.5.1`.
