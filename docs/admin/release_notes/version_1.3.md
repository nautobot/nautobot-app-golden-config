# v1.3 Release Notes

- Add the ability to update Intended Configuration for multiple use cases, supporting rendering of secrets out of the box.
- Enable Routine Testing Against Upstream Nautobot versions to ensure continuous compatibility.

## v1.3.0 - 2022-12

### Added

- [#344](https://github.com/nautobot/nautobot-plugin-golden-config/issues/344) - Enable routine testing against upstream Nautobot versions to ensure continuous compatibility.
- [#339](https://github.com/nautobot/nautobot-plugin-golden-config/issues/339) - Add the ability to post-process Intended Configuration for multiple use cases, supporting rendering of secrets out of the box.

### Changed

- [#378](https://github.com/nautobot/nautobot-plugin-golden-config/issues/378) - Update nornir job logging to provide more feedback on the steps that are taking place.
- [#365](https://github.com/nautobot/nautobot-plugin-golden-config/issues/365) - Add slack notify after release to Github Actions workflow.

### Fixed

- [#369](https://github.com/nautobot/nautobot-plugin-golden-config/issues/369) - Fix issue with runner serial resulting in `InterfaceError: connection already closed` error.
- [#398](https://github.com/nautobot/nautobot-plugin-golden-config/issues/398) - Fix incorrect relative link in app_feature_compliance.md.
