# Upgrade

When a new release comes out it may be necessary to run a migration of the database to account for any changes in the data models used by this plugin. Execute the command nautobot-server migrate from the Nautobot install nautobot/ directory after updating the package.

## v1.0.0
v1.0.0 Provides a breaking change for users utilising the `Backup Repository Matching Rule` and `Intended Repository Matching Rule` features. Migration script will only migrate the first repository from the list into the new default settings.
 
Because of this specific behaviour, please review your configuration and capture it before attempting to upgrade if using above features.

### Changed
- [#205](https://github.com/nautobot/nautobot-plugin-golden-config/pull/205) - Multiple Golden Config Settings
