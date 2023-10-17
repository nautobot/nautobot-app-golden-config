# Compatibility Matrix

Changes to the support of upstream Nautobot releases will be announced 1 minor or major version ahead.

The **deprecation policy** will be announced within the [release notes](./release_notes/index.md), and updated in the table below. There will be a `stable-<major>.<minor>` branch that will be minimally maintained. Any security enhancements or major bugs in that branch will be supported for a limited time.

While that last supported version will not be strictly enforced via the `max_version` setting, any issues with an updated Nautobot supported version in a minor release will require raising a bug and fixing it in Nautobot core, with no fixes expected in this plugin. This allows the Golden Config plugin the ability to quickly take advantage of the latest features in Nautobot.

| Golden Config Version | Nautobot First Support Version | Nautobot Last Support Version |
| ------------- | -------------------- | ------------- |
| 1.0.X         | 2.0.0                | 1.99.99        |
