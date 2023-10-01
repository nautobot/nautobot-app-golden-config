# Troubleshooting Dispatchers

At a high-level the default dispatchers that Golden Config uses are actually sourced from another open source library. [nornir-nautobot](https://docs.nautobot.com/projects/nornir-nautobot/en/latest/) contains the Nornir tasks that define the methods that Golden Config utilizes.

## Dispatcher Sender

This dispatcher task is explained in the [nornir-nautobot docs](https://docs.nautobot.com/projects/nornir-nautobot/en/latest/task/task/), but provided here is a simple overview.

- If exists check `custom_dispatcher`, for network_driver, if a custom_dispatcher is used but not found, fail immediately
- Check for framework & driver `f"nornir_nautobot.plugins.tasks.dispatcher.{network_driver}.{framework.title()}{network_driver_title}"`
- Check for default, e.g. `f"nornir_nautobot.plugins.tasks.dispatcher.default.{framework.title()}Default"`

!!! info
    Where `framework` is a library like `netmiko` or `napalm` and `network_driver` is the platform like `cisco_ios` or `arista_eos`.

### Cannot import <os> is the library installed?

This occurs when a Golden Config job is executed with a Nautobot `platform`, and that platform network_driver is not found for the Nornir "method" the job is attempting to run.

_How is the dispatcher loaded?_ Please review the 3 previous sections for understanding how it is is loaded.

This error is actually generated [here](https://github.com/napalm-automation/napalm/blob/50ab9f73a2afd8c84c430e5d844e570f28adc917/napalm/base/__init__.py#L100C17-L100C17) in the NAPALM core code.

Some steps to consider to troubleshooting this:

1. PIP install the NAPALM plugin into the Nautobot environment from PYPI. 

    As an example if you wanted to use NAPALMs Palo Alto plugin you'd need that library installed in the environment.

    ```shell
    pip install napalm-panos
    ```

2. Is the platform network_driver being used something that is handled by default?

    Check the default dispatcher network os driver name. Change your platform's network_driver to match the default naming which is following the driver names from Netmiko.
