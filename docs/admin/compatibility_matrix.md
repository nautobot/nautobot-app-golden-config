# Compatibility Matrix

Changes to the support of upstream Nautobot releases will be announced 1 minor or major version ahead.

The **deprecation policy** will be announced within the [release notes](./release_notes/index.md), and updated in the table below. There will be a `stable-<major>.<minor>` branch that will be minimally maintained. Any security enhancements or major bugs in that branch will be supported for a limited time.

While that last supported version will not be strictly enforced via the `max_version` setting, any issues with an updated Nautobot supported version in a minor release will require raising a bug and fixing it in Nautobot core, with no fixes expected in this app. This allows the Golden Config App the ability to quickly take advantage of the latest features in Nautobot.

| Golden Config Version | Nautobot First Support Version | Nautobot Last Support Version |
| --------------------- | ------------------------------ | ----------------------------- |
| 0.9.X                 | 1.0.0                          | 1.2.99 [Official]             |
| 0.10.X                | 1.0.0                          | 1.2.99 [Official]             |
| 1.0.X                 | 1.2.0                          | 1.3.99 [Official]             |
| 1.1.X                 | 1.2.0                          | 1.3.99 [Official]             |
| 1.2.X                 | 1.4.0                          | 1.5.2 [Official]              |
| 1.3.X                 | 1.4.0                          | 1.5.2 [Official]              |
| 1.4.X                 | 1.5.3                          | 1.5.99 [Official]             |
| 1.5.X                 | 1.6.1                          | 1.6.99 [Official]             |
| 1.6.X                 | 1.6.1                          | 1.6.99 [Official]             |
| 2.0.x                 | 2.0.0                          | 2.3.99 [Official]             |
| 2.1.x                 | 2.0.0                          | 2.3.99 [Official]             |
| 2.2.x                 | 2.0.0                          | 2.3.99 [Official]             |
| 2.3.x                 | 2.4.2                          | 2.4.99                        |