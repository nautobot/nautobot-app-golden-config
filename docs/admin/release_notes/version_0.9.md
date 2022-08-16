# v0.9 Release Notes

- Initial release

## v0.9.10 - 2021-11

### Announcements

- Nautobot Golden Config 0.9.X will officially not support versions after 1.2.X
- Nautobot Golden Config 1.0.X will tentatively not support versions after 1.2.X
- Nautobot Golden Config will maintain a `stable-<major>.<minor>` branch name
- Nautobot Golden Config branching policy created

### Added

- [#155](https://github.com/nautobot/nautobot-plugin-golden-config/issues/155) Contribution policy updated in Readme

### Fixed

- [#129](https://github.com/nautobot/nautobot-plugin-golden-config/issues/129) Update filters, forms, add filters to api.
- [#148](https://github.com/nautobot/nautobot-plugin-golden-config/issues/148) move diff2html to be locally served
- [#154](https://github.com/nautobot/nautobot-plugin-golden-config/issues/154) Fix report bar chart overlap
- [#161](https://github.com/nautobot/nautobot-plugin-golden-config/issues/161) Fix configuration compliance export gives traceback
- [#164](https://github.com/nautobot/nautobot-plugin-golden-config/issues/164) Fixes the export functionality for configuration compliance list view.
- [#166](https://github.com/nautobot/nautobot-plugin-golden-config/issues/166) fix configuration and overview reporting csv exports

## v0.9.9 - 2021-10

### Fixed

- [#146](https://github.com/nautobot/nautobot-plugin-golden-config/issues/146) Removed custom fields from showing in Configuration Overview ListView.
- [#145](https://github.com/nautobot/nautobot-plugin-golden-config/issues/145) Rename all Filterset to be compliant with Nautobot naming convention.
- [#143](https://github.com/nautobot/nautobot-plugin-golden-config/issues/143) Added appropriate metadata tag to jobs.

## v0.9.8 - 2021-10

### Fixed

- Fixing missing and extra fields, for edge cases.
- Replace enable_golden with enable_intended in default settings.

## v0.9.7 - 2021-09

### Fixed

- [#130](https://github.com/nautobot/nautobot-plugin-golden-config/issues/130) SSH Sessions does not die with celery workers, by adding context manager [#128](https://github.com/nautobot/nautobot-plugin-golden-config/pull/128)
- [#125](https://github.com/nautobot/nautobot-plugin-golden-config/issues/125) Update search filterset

### Added

- [#126](https://github.com/nautobot/nautobot-plugin-golden-config/issues/126) Add more robust checking for platform
- [#115](https://github.com/nautobot/nautobot-plugin-golden-config/issues/115) Update docs to be more clear on how to use config context

## v0.9.6 - 2021-09

### Fixed

- [#95](https://github.com/nautobot/nautobot-plugin-golden-config/issues/95) Fix credential escaping issues on Git
- [#113](https://github.com/nautobot/nautobot-plugin-golden-config/issues/113) Clean up and normalize GraphQL decorator
- [#41](https://github.com/nautobot/nautobot-plugin-golden-config/issues/41) Fail Gracefully when platform is missing or wrong, bump nautobot-plugin-nornir version
- [#104](https://github.com/nautobot/nautobot-plugin-golden-config/issues/104) Fail Gracefully when Device queryset is empty
- [#109](https://github.com/nautobot/nautobot-plugin-golden-config/issues/109) Account for Nautobot 1.0/1.1 template change

### Added

- [#103](https://github.com/nautobot/nautobot-plugin-golden-config/issues/103) Add manage commands for jobs
- [#108](https://github.com/nautobot/nautobot-plugin-golden-config/issues/108) Update docs and add quick start guide
- [#105](https://github.com/nautobot/nautobot-plugin-golden-config/issues/105) Added structure data config compliance
- [#119](https://github.com/nautobot/nautobot-plugin-golden-config/issues/119) Migrate to Github Actions
- [#121](https://github.com/nautobot/nautobot-plugin-golden-config/issues/121) Moved to Celery for development environment
- Added Mysql to development environment

## v0.9.5 - 2021-07

### Fixed

- Loosen Nautobot version

## v0.9.4 - 2021-06

### Added

- [#87](https://github.com/nautobot/nautobot-plugin-golden-config/issues/87) Added the ability to map arbitraty slug to proper netutils expected network_os

### Fixed

- [#87](https://github.com/nautobot/nautobot-plugin-golden-config/issues/87) Dispatcher docs and update dependency for nautobot-plugin-nornir

## v0.9.3 - 2021-06-19

### Added

 - Added changelog
 - [#74](https://github.com/nautobot/nautobot-plugin-golden-config/issues/74) Added hover text to icon on plugin home screen
 - [#84](https://github.com/nautobot/nautobot-plugin-golden-config/issues/84) Added auto-deploy to PyPI

### Fixed

- [#72](https://github.com/nautobot/nautobot-plugin-golden-config/issues/72) Fix uniqueness constraint on update_or_create of config compliance model
- [#75](https://github.com/nautobot/nautobot-plugin-golden-config/issues/75) Updated doc for various images and links
- [#80](https://github.com/nautobot/nautobot-plugin-golden-config/issues/80) Fix navigation when not using compliance
- [#81](https://github.com/nautobot/nautobot-plugin-golden-config/issues/81) Fix settings to set to null instead cascade on delete when removing git repo
