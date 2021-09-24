# Changelog

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