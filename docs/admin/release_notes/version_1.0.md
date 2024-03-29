# v1.0 Release Notes

- Added support for Jinja2Filters to be be used in configuration generation
- Added support for multiple repos
- Add Git datasource to load GC properties
- Added support for nautobot secrets group on git repos
- Changed the release policy
- Updated navigation to a dedicated top level menu

## v1.0.3 - 2022-06

### Fixed

- [#257](https://github.com/nautobot/nautobot-app-golden-config/issues/257) Resolved template_content displaying SoT AGG link on Device detail page if Device not in scope of GoldenConfigSetting
    - Change to pull version from package instead of static variable

## v1.0.2 - 2022-05

### Fixed

- [#246](https://github.com/nautobot/nautobot-app-golden-config/issues/246) Dependabot update to Docker redis-7.x
- [#233](https://github.com/nautobot/nautobot-app-golden-config/issues/233) Dependabot update to paramiko-2.10.1
- [#251](https://github.com/nautobot/nautobot-app-golden-config/issues/251) Add description to CSV config replace export

## v1.0.1 - 2022-05

### Fixed

- [#238](https://github.com/nautobot/nautobot-app-golden-config/issues/238) Fixed repo/docs/homepage links for PyPI
- [#243](https://github.com/nautobot/nautobot-app-golden-config/issues/243) Removing unneed javascript source as it is part of [#243](https://github.com/nautobot/nautobot-app-golden-config/pull/243)

## v1.0.0 - 2022-04

### Added

- [#180](https://github.com/nautobot/nautobot-app-golden-config/issues/180) Added Renovate for proactive package management
- [#158](https://github.com/nautobot/nautobot-app-golden-config/issues/158) Allow for Jinja2 Filters to be used by GoldenConfig templates
- [#167](https://github.com/nautobot/nautobot-app-golden-config/issues/167) Added support for multiple repos
- [#205](https://github.com/nautobot/nautobot-app-golden-config/issues/205) Added support for multiple repos via multiple golden config settings
- [#206](https://github.com/nautobot/nautobot-app-golden-config/issues/206) Add Git datasource to load GC properties
- [#218](https://github.com/nautobot/nautobot-app-golden-config/issues/218) Added ability to storre SoTAgg field leveraging Nautobot saved GraphQl query
- [#225](https://github.com/nautobot/nautobot-app-golden-config/issues/225) Added support for nautobot secrets group on git repos
- [#234](https://github.com/nautobot/nautobot-app-golden-config/issues/234) Minor update to FAQ

### Changed

- [#171](https://github.com/nautobot/nautobot-app-golden-config/issues/171) Changed the release policy
- [#158](https://github.com/nautobot/nautobot-app-golden-config/issues/158) Changed variable job_result to nautobot_job
- [#186](https://github.com/nautobot/nautobot-app-golden-config/issues/186) Update mariadb Docker tag to v10.7
- [#187](https://github.com/nautobot/nautobot-app-golden-config/issues/187) Update postgres Docker tag to v14
- [#188](https://github.com/nautobot/nautobot-app-golden-config/issues/188) Update Markdown dependency
- [#190](https://github.com/nautobot/nautobot-app-golden-config/issues/190) Update to Nautobot 1.2.0
- [#190](https://github.com/nautobot/nautobot-app-golden-config/issues/190) Remove Nautobot 1.0 specific code
- [#211](https://github.com/nautobot/nautobot-app-golden-config/issues/211) Update dependency mariadb to v10.8
- [#229](https://github.com/nautobot/nautobot-app-golden-config/issues/229) Updated navigation to a dedicated top level menu

### Fixed

- [#176](https://github.com/nautobot/nautobot-app-golden-config/issues/176) Fixed Pylint issue
- [#182](https://github.com/nautobot/nautobot-app-golden-config/issues/182) Add reference to Nornir app for installation
- [#183](https://github.com/nautobot/nautobot-app-golden-config/issues/183) Fixed documentation for sot_agg_transposer default
- [#184](https://github.com/nautobot/nautobot-app-golden-config/issues/184) Fix markdown links in quick-start
- [#194](https://github.com/nautobot/nautobot-app-golden-config/issues/194) Detailed Error Handling in get_job_filter helper
- [#229](https://github.com/nautobot/nautobot-app-golden-config/issues/229) Fixed [#165](https://github.com/nautobot/nautobot-app-golden-config/pull/165), Configuration Compliance List View "Device" filter doesn't work
