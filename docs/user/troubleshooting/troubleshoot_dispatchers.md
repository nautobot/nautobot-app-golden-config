# Troubleshooting Dispatchers

At a high-level the default dispatchers that Golden Config uses are actually sourced from another open source library. [nornir-nautobot](https://docs.nautobot.com/projects/nornir-nautobot/en/latest/) contains the Nornir tasks that define the methods that Golden Config utilizes.

This dispatcher task is explained in the [nornir-nautobot docs](https://docs.nautobot.com/projects/nornir-nautobot/en/latest/task/task/)

Golden config uses the `get_dispatcher()` function from the Nautobot Plugin Nornir plugin. General information on dispatchers can be found in the [dispatcher](https://docs.nautobot.com/projects/plugin-nornir/en/latest/user/app_feature_dispatcher/) documentation.

Although this functionality is simply used by Golden Config and isn't directly developed within this application the below troubleshooting sections may help.

### Cannot import <os> is the library installed?

This occurs when a Golden Config job is executed with a Nautobot `platform`, and that platform network_driver is not found for the Nornir "method" the job is attempting to run.

How is the dispatcher loaded?

1. Job initializes Nornir and the method is called with `get_dispatcher()` function from Nautobot-Plugin-Nornir.
2. Nornir initialization looks in the DEFAULT_DISPATCHER map for the platform network_driver from [nornir-nautobot](https://github.com/nautobot/nornir-nautobot/blob/64baa8a24d21d9ec14c32be569e2b51cd0bd1cd1/nornir_nautobot/plugins/tasks/dispatcher/__init__.py#L12) mapping.
3. Merge this mapping with anything directly configured in Golden Config [dispatcher mapping]().
4. Load the dispatcher based on network_driver, or load the default dispatcher if the dictionary mapping doesn't include it.
5. The default dispatcher by default uses NAPALM and attempts to load the **getter**. Alternatively there is a `default_netmiko` dispatcher that will default to loading the driver via Netmiko instead of NAPALM.

This error is actually generated [here](https://github.com/napalm-automation/napalm/blob/50ab9f73a2afd8c84c430e5d844e570f28adc917/napalm/base/__init__.py#L100C17-L100C17) in the NAPALM core code.

Some steps to consider to troubleshooting this:

1. PIP install the NAPALM plugin into the Nautobot environment from PYPI. 

    As an example if you wanted to use NAPALMs Palo Alto plugin you'd need that library installed in the environment.

    ```shell
    pip install napalm-panos
    ```

2. Is the platform network_driver being used something that is handled by default?

    Check the default dispatcher network os driver name. Change your platform's network_driver to match the default naming which is following the driver names from Netmiko.
