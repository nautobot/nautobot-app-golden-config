# Troubleshooting Overview

In an effort to help with troubleshooting, each expected error, will now emit an error ID, in the format of `E3XXX`, such as `E3003: There is currently no CLI-config parser support for platform network_driver `{obj.platform.network_driver}`, preemptively failed.`. The idea will be to define the error, the error message and some recommended troubleshooting steps or even potentially some fixes.

This is an ongoing effort, but the foundation has been built.

Within the Nautobot ecosystem, you may see various errors, they are distributed between 3 libraries as followed.

| Error Range | Plugin Docs |
| ----------- | ----------- |
| E1001-E1999 | [Nornir Nautobot](https://docs.nautobot.com/projects/nornir-nautobot/en/latest/task/troubleshooting/) |
| E2001-E2999 | [Nautobot Plugin Nornir](https://docs.nautobot.com/projects/plugin-nornir/en/latest/admin/troubleshooting/) |
| E3001-E3999 | [Nautobot Golden Config](https://docs.nautobot.com/projects/golden-config/en/latest/admin/troubleshooting/) |