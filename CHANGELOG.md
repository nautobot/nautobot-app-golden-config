# Changelog

## v1.0.3 - 2022-06

### Fixed

- #257 Resolved template_content displaying SoT AGG link on Device detail page if Device not in scope of GoldenConfigSetting
- Change to pull version from package instead of static variable

## v1.0.2 - 2022-05

### Fixed

- #246 Dependabot update to Docker redis-7.x
- #233 Dependabot update to paramiko-2.10.1
- #251 Add description to CSV config replace export

## v1.0.1 - 2022-05

### Fixed

- #238 Fixed repo/docs/homepage links for PyPI
- #243 Removing unneed javascript source as it is part of #243

## v1.0.0 - 2022-04

### Announcements

- Nautobot Golden Config 1.0.X will officially only support versions 1.2.0 - 1.3.99

### Added

- #180 Added Renovate for proactive package management
- #158 Allow for Jinja2 Filters to be used by GoldenConfig templates 
- #167 Added support for multiple repos
- #205 Added support for multiple repos via multiple golden config settings
- #206 Add Git datasource to load GC properties
- #218 Added ability to storre SoTAgg field leveraging Nautobot saved GraphQl query
- #225 Added support for nautobot secrets group on git repos
- #234 Minor update to FAQ

### Changed

- #171 Changed the release policy
- #158 Changed variable job_result to nautobot_job
- #186 Update mariadb Docker tag to v10.7
- #187 Update postgres Docker tag to v14
- #188 Update Markdown dependency
- #190 Update to Nautobot 1.2.0
- #190 Remove Nautobot 1.0 specific code
- #211 Update dependency mariadb to v10.8 
- #229 Updated navigation to a dedicated top level menu

### Fixed

- #176 Fixed Pylint issue
- #182 Add reference to Nornir plugin for installation
- #183 Fixed documentation for sot_agg_transposer default
- #184 Fix markdown links in quick-start
- #194 Detailed Error Handling in get_job_filter helper
- #229 Fixed #165, Configuration Compliance List View "Device" filter doesn't work

## v0.9.10 - 2021-11

### Announcements

- Nautobot Golden Config 0.9.X will officially not support versions after 1.2.X
- Nautobot Golden Config 1.0.X will tentatively not support versions after 1.2.X
- Nautobot Golden Config will maintain a `stable-<major>.<minor>` branch name
- Nautobot Golden Config branching policy created

### Added

- #155 Contribution policy updated in Readme

### Fixed

- #129 Update filters, forms, add filters to api.
- #148 move diff2html to be locally served
- #154 Fix report bar chart overlap
- #161 Fix configuration compliance export gives traceback
- #164 Fixes the export functionality for configuration compliance list view.
- #166 fix configuration and overview reporting csv exports

## v0.9.9 - 2021-10

### Fixed

- #146 Removed custom fields from showing in Configuration Overview ListView.
- #145 Rename all Filterset to be compliant with Nautobot naming convention.
- #143 Added appropriate metadata tag to jobs.

## v0.9.8 - 2021-10

### Fixed

- Fixing missing and extra fields, for edge cases.
- Replace enable_golden with enable_intended in default settings.

## v0.9.7 - 2021-09

### Fixed

- #130 SSH Sessions does not die with celery workers, by adding context manager #128
- #125 Update search filterset

### Added 

- #126 Add more robust checking for platform
- #115 Update docs to be more clear on how to use config context
## v0.9.6 - 2021-09

### Fixed

- #95 Fix credential escaping issues on Git
- #113 Clean up and normalize GraphQL decorator
- #41 Fail Gracefully when platform is missing or wrong, bump nautobot-plugin-nornir version
- #104 Fail Gracefully when Device queryset is empty
- #109 Account for Nautobot 1.0/1.1 template change

### Added 

- #103 Add manage commands for jobs
- #108 Update docs and add quick start guide
- #105 Added structure data config compliance
- #119 Migrate to Github Actions
- #121 Moved to Celery for development environment
- Added Mysql to development environment

## v0.9.5 - 2021-07

### Fixed

- Loosen Nautobot version

## v0.9.4 - 2021-06

### Added

- #87 Added the ability to map arbitraty slug to proper netutils expected network_os

### Fixed

- #87 Dispatcher docs and update dependency for nautobot-plugin-nornir

## v0.9.3 - 2021-06-19

### Added

 - Added changelog
 - #74 Added hover text to icon on plugin home screen
 - #84 Added auto-deploy to PyPI

### Fixed

- #72 Fix uniqueness constraint on update_or_create of config compliance model
- #75 Updated doc for various images and links
- #80 Fix navigation when not using compliance 
- #81 Fix settings to set to null instead cascade on delete when removing git repo