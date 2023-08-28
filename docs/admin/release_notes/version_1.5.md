# v1.5 Release Notes

- Add ability to update JSON based compliance via a job and have git integrations.
- Made custom compliance a boolean to support both JSON or CLI custom compliance types.
- Add metrics for Golden Config plugin.
- Supports Nautobot >=1.6.1,<2.0.0.

## v1.5.0 - 2023-08

### Added

- [455](https://github.com/nautobot/nautobot-plugin-golden-config/pull/455) - Add metrics for Golden Config plugin.
- [485](https://github.com/nautobot/nautobot-plugin-golden-config/pull/485) - Custom compliance for CLI and JSON rules.
- [487](https://github.com/nautobot/nautobot-plugin-golden-config/pull/487) - Implement native JSON support.

### Changed

- [485](https://github.com/nautobot/nautobot-plugin-golden-config/pull/485) - Changed the behavior of custom compliance to a boolean vs toggle between cli, json, and custom.

### Fixed

- [505](https://github.com/nautobot/nautobot-plugin-golden-config/pull/505) - fixes imports and choice definitions in the compliance nornir play.
- [513](https://github.com/nautobot/nautobot-plugin-golden-config/pull/513) - Fixed issue with native JSON support with `get_config_element` function.
