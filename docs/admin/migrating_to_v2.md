# Migrating to v2

While not a replacement of the [Nautobot Migration guide](https://docs.nautobot.com/projects/core/en/stable/development/apps/migration/from-v1/) these migration steps specifically for Golden Config are pretty straight forward, here is a quick overview with details information below.

1. Ensure `Platform.network_driver` is set on every `Platform` object you have, in most circumstances running `nautobot-server populate_platform_network_driver` will take care of it.
2. Remove any reference to `slug` as well as to the models `Region`, `Site`, `DeviceRole`, or `RackRole` in your **Dynamic Group** definition, in most circumstances running `nautobot-server audit_dynamic_groups` will guide you to what needs to change.
3. Remove any reference to `slug` (or change to network_driver) as well as to the models `Region`, `Site`, `DeviceRole`, or `RackRole` in your **GraphQL** definition and reflect those changes in your Jinja files.
4. Remove any reference to `slug` as well as to the models `Region`, `Site`, `DeviceRole`, or `RackRole` in your **Golden Config Setting** definition in all of `Backup Path`, `Intended Path`, and `Template Path`. 
5. Remove any `dispatcher_mapping` settings you have in your `nautobot_config.py` settings, see Golden Config for alternative options.
6. Update your Git Repositories to use Nautobot Secrets.

!!! warning
    Before you start, please note the `nautobot-server populate_platform_network_driver` command **must be ran in Nautobot 1.6.2 -> 1.6.X** as it will not work once on Nautobot 2.0.

These steps may range from no change (though unlikely) to large amount of change with your environment in order to successfully upgrade Golden Config. To help guide you, there is a detailed explanation and question to ask yourself if these changes will effect you or not.

**Providing Context**

There are 3 primary pieces of information that will effect most of the changes that will need to be made, here is a recap of them.

- In Nautobot 2.0.0, all the `Region` and `Site` related data models are being migrated to use `Location`. 
- The `ipam.Role`, `dcim.RackRole`, and `dcim.DeviceRole` models have been removed and replaced by a single `extras.Role` model. This means that any references to the removed models in the code now use the `extras.Role` model instead.
- Slugs were used to identify unique objects in the database for various models in Nautobot v1.x and they are now replaced by Natural Keys or can often get the same effect adding the `|slugify` filter to your data.

## Platform Network Driver

!!! tip
    You can safely skip this section if you already have your `Platform.network_driver` set and were not using either `platform_slug_map` nor `dispatcher_mapping` settings.

The `Platform.slug` has been replace by Nautobot's `Platform.network_driver`. The nice thing about this feature is it provides mappings to all of the major network library (or frameworks) such as Netmiko and NAPALM to properly map between the slightly different names each library provides, such as `cisco_ios` vs `ios`. However, that means that you must now provide the network_driver on the the Platform object.

While still on the a Nautobot 1.6 instance, run the command `nautobot-server populate_platform_network_driver`, this will help map all of your `Platform.slug`'s to `Platform.network_driver`. If there are any Platform's missed, you must update the Platform definitions that will be used by Golden Config.

If previously you have leveraged the `platform_slug_map` you likely only have to assign the `network_driver` to your multiple current platforms. In the unlikely chance that you have a requirement to override the default network_driver_mappings, you can do so with the [NETWORK_DRIVERS](https://docs.nautobot.com/projects/core/en/stable/user-guide/administration/configuration/optional-settings/?h=network_driver#network_drivers) settings via UI with the [constance settings](../user/app_getting_started.md#constance-settings).

If previously you have leveraged the `dispatcher_mapping` to use your preferred network library or framework such as Netmiko or NAPALM, you can how use the [constance settings](../user/app_getting_started.md#constance-settings) via the UI.

!!! info
    If you were using the `dispatcher_mapping` for other reasons, see the section below for Custom Dispatcher.

## Dynamic Group

!!! tip
    You can safely skip this section if your Dynamic Groups was not using slugs/Site/Region/DeviceRole or your Dynamic Groups are currently in the required state.

In an effort to guide you along, you are highly encouraged to leverage the `nautobot-server audit_dynamic_groups` as [documented](https://docs.nautobot.com/projects/core/en/v2.0.0/user-guide/administration/tools/nautobot-server/#audit_dynamic_groups). You will know you have completed this step, when the scope of devices in your Dynamic Group match your expectations.

## GraphQL

!!! tip
    You can safely skip this section if your GraphQL Query was not using slugs/Site/Region/DeviceRole or your saved GraphQL Query currently renders to the appropriate state.

As mentioned, any reference to slug or to one of the removed models will need to be updated to reflect Nautobot 2.0 standards, in this example we will review what would need to change.

```
query ($device_id: ID!) {
  device(id: $device_id) {
    hostname: name
    tenant {
      name
      slug          <----- Remove slug
    }
    tags {
      name
      slug          <----- Remove slug
    }
    device_role {   <----- Change to role vs device_role
      name
    }
    platform {
      name
      slug          <----- change to network_driver and potentially add network_driver_mappings
    }
    site {
      name
      slug          <----- Remove slug
    }
  }
}
```

The new query would end up being:

```
query ($device_id: ID!) {
  device(id: $device_id) {
    hostname: name
    tenant {
      name
    }
    tags {
      name
    }
    role {
      name
    }
    platform {
      name
      network_driver
    }
    site {
      name
      slug
    }
  }
}
```

Additionally, your Jinja 2 templates will need to be updated to reflect the new updates to the data. Fortunately, if you have accepted the default that `SlugField` returns, this may be as simple as adding as the `| slugify` Jinja filter to the name equivalent. Let's take a quick look at a few examples of Jinja file change you may need to make:

_Using slugify_

```jinja
snmp-server location {{ site.slug }}             <---- old way of doing it
snmp-server location {{ site.name | slugify }}   <---- new way of doing it
```
_Update model_

```jinja
{% if device_role.name == 'spine' %}             <---- old way of doing it
{% if role.name == 'spine' %}                    <---- new way of doing it
```

_Use network_driver_

```jinja
{% if platform.slug == 'cisco_ios' %}            <---- old way of doing it
{% if platform.network_driver == 'cisco_ios' %}  <---- new way of doing it
```

## Golden Config Settings

!!! tip
    You can safely skip this section if you are not using slug or one of the Models in your `Backup Path`, `Intended Path`, and `Template Path` settings.

Similar to the the jinja examples above, you must ensure that the slug and legacy models are not referenced, using the previous recommendations and comparing to the current recommendations we can see how to make these changes.

_Path for backup and intended_

```jinja
{{obj.site.slug}}/{{obj.name}}                   <---- old way of doing it
{{obj.location.name|slugify}}/{{obj.name}}       <---- new way of doing it
```

_Path for templates_

```jinja
{{obj.platform.slug}}.j2                         <---- old way of doing it
{{obj.platform.network_driver}}.j2               <---- new way of doing it
```

## Custom Dispatcher

!!! tip
    You can safely skip this section if you have not been using `dispatcher_mapping` settings.

If you have previously used the `dispatcher_mapping` settings to prefer the framework (such as netmiko or napalm), please see the Platform Network Driver section above. If you were truly "rolling your own dispatcher", then it is simply a matter of updating your settings.

The `custom_dispatcher` settings are Golden Config settings (and **NOT** Nautobot Plugin Nornir settings), and the key name is `custom_dispatcher`. For your protection, the application will not start if you have either `dispatcher_mapping` or `custom_dispatcher` in Nautobot Plugin Nornir.

Previous relevant Settings:

```python
PLUGINS_CONFIG = {
    "nautobot_plugin_nornir": {
        "dispatcher_mapping": {
            "arista_eos": "my_custom.dispatcher.NornirDriver",
            "arbitrary_platform_name": "my_custom.dispatcher.OtherNornirDriver",
        },
    },
    "nautobot_golden_config": {
    },
}
```

Current relevant Settings:

```python
PLUGINS_CONFIG = {
    "nautobot_plugin_nornir": {
    },
    "nautobot_golden_config": {
        "custom_dispatcher": {            # <---- Nested under nautobot_golden_config
            "arista_eos": "my_custom.dispatcher.NornirDriver",
            "arbitrary_platform_name": "my_custom.dispatcher.OtherNornirDriver",
        },

    },
}
```

The [custom dispatcher docs](../admin/admin_install.md#custom-dispatcher) will provide further clarification if needed.

## Secrets

!!! tip
    You can safely skip this section if you have already been using Nautobot Secrets and not Git Repository Token.

Nautobot initially had the ability to store some secrets, this was deprecated when [Secrets framework](https://docs.nautobot.com/projects/core/en/stable/user-guide/platform-functionality/secret/) was added in Nautobot 1.2. The feature to directly store Secrets in the database has been removed in 2.0.

The documentation has been updated in docs covering [secret groups](../user/app_use_cases.md#create-secret-groups).