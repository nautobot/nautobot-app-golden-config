# v1.4 Release Notes

- Change min version of Nautobot from 1.4.0 to 1.5.3 which is required for the use of NautobotUIViewset, Notes mixins etc.

## v1.4.2 - 2023-08

### Changed

- [519](https://github.com/nautobot/nautobot-plugin-golden-config/pull/519) - docs-only: large fixes and template troubleshooting section.

### Fixed

- [492](https://github.com/nautobot/nautobot-plugin-golden-config/pull/492) - Fix count of in scope devices on settings detail view.
- [498](https://github.com/nautobot/nautobot-plugin-golden-config/pull/498) - Fix deepdiff dependency.
- [501](https://github.com/nautobot/nautobot-plugin-golden-config/pull/501) - Update docs for adding CustomField data with datasources.
- [503](https://github.com/nautobot/nautobot-plugin-golden-config/pull/503) - Switch from deprecated FilterSet to new FilterSetMixin.
- [504](https://github.com/nautobot/nautobot-plugin-golden-config/pull/504) - Fix extend queryfilter to export.
- [511](https://github.com/nautobot/nautobot-plugin-golden-config/pull/511) - Fix `log_failure` function missing argument.
- [523](https://github.com/nautobot/nautobot-plugin-golden-config/pull/523) - Fix docs site by pinning dev dependencies.
- [530](https://github.com/nautobot/nautobot-plugin-golden-config/pull/530) - Fix, removing ConfigCompliance model import from 0005 migration.

## v1.4.1 - 2023-05

### Fixed

- [488](https://github.com/nautobot/nautobot-plugin-golden-config/pull/488) - Fix Golden Config Settings Buttons.

## v1.4.0 - 2023-05

### Added

- [445](https://github.com/nautobot/nautobot-plugin-golden-config/pull/445) - Add validation for Settings sot_agg_query.
- [449](https://github.com/nautobot/nautobot-plugin-golden-config/pull/449) - Allows for custom kwargs to `get_secret_by_secret_group_slug`.
- [470](https://github.com/nautobot/nautobot-plugin-golden-config/pull/470) - Enhance UI settings detail object view.
- [473](https://github.com/nautobot/nautobot-plugin-golden-config/pull/473) - Add status selection field to job filtering.
- [480](https://github.com/nautobot/nautobot-plugin-golden-config/pull/480) - Add compliance summary to default tenant view.

### Changed

- [414](https://github.com/nautobot/nautobot-plugin-golden-config/pull/414) - Update application description for UI.
- [407](https://github.com/nautobot/nautobot-plugin-golden-config/pull/407) - Update branching policy in contributing docs.
- [417](https://github.com/nautobot/nautobot-plugin-golden-config/pull/417) - Changed extends base.html to extends generic/object_detail.html.
- [434](https://github.com/nautobot/nautobot-plugin-golden-config/pull/434) - Upgrade deepdiff dependency to 6.2.0.
- [451](https://github.com/nautobot/nautobot-plugin-golden-config/pull/451) - Tune Dependabot.
- [459](https://github.com/nautobot/nautobot-plugin-golden-config/pull/459) - Update tasks.py to meet current standards.
- [464](https://github.com/nautobot/nautobot-plugin-golden-config/pull/464) - Update ordering on compliance views.
- [471](https://github.com/nautobot/nautobot-plugin-golden-config/pull/471) - Migrate to using NautobotUIViewset and other initial 2.x prep work.
- [481](https://github.com/nautobot/nautobot-plugin-golden-config/pull/481) - Update filtersets for rack-group to extend proper TreeNode parent.

### Fixed

- [436](https://github.com/nautobot/nautobot-plugin-golden-config/pull/436) - Update FAQ for how compliance works.
- [444](https://github.com/nautobot/nautobot-plugin-golden-config/pull/444) - `app_faq.md` references incorrect `Cisco IOS XR` platform slug.
- [446](https://github.com/nautobot/nautobot-plugin-golden-config/pull/446) - Fix mysql not working in github actions.
- [450](https://github.com/nautobot/nautobot-plugin-golden-config/pull/450) - Make ConfigReplace export match import.
- [456](https://github.com/nautobot/nautobot-plugin-golden-config/pull/456) - Fix postprocessing to use Sandbox Jinja2 environment.
- [461](https://github.com/nautobot/nautobot-plugin-golden-config/pull/461) - Moves dependabot config to proper location.
- [463](https://github.com/nautobot/nautobot-plugin-golden-config/pull/463) - Fix Json render in compliance reporting template.
- [468](https://github.com/nautobot/nautobot-plugin-golden-config/pull/468) - Fix GoldenConfig list view and csv export.
- [474](https://github.com/nautobot/nautobot-plugin-golden-config/pull/474) - Docs update: Fix multiple typos.
