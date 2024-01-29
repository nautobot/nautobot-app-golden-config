# Upgrading the App

Here you will find any steps necessary to upgrade the App in your Nautobot environment.

## Upgrade Guide

!!! warning "Developer Note - Remove Me!"
    Add more detailed steps on how the app is upgraded in an existing Nautobot setup and any version specifics (such as upgrading between major versions with breaking changes).

When a new release comes out it may be necessary to run a migration of the database to account for any changes in the data models used by this app. Execute the command `nautobot-server post-upgrade` within the runtime environment of your Nautobot installation after updating the `nautobot-golden-config` package via `pip`.
