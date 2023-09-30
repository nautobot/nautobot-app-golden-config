# Migrating to v2

The migration steps are pretty straight forward, here is a quick overview with details information below.

1. Ensure `Platform.network_driver` is set on every `Platform` object you have, in most circumstances running `nautobot-server populate_platform_network_driver` will take care of it.
2. Remove any reference to `slug` as well as to the models `Region`, `Site`, `DeviceRole`, or `RackRole` in your **Dynamic Group** definition, in most circumstances running `nautobot-server audit_dynamic_groups` will guide you to what needs to change.
3. Remove any reference to `slug` (or change to network_driver) as well as to the models `Region`, `Site`, `DeviceRole`, or `RackRole` in your **GraphQL** definition and reflect those changes in your Jinja files.
4. Remove any reference to `slug` as well as to the models `Region`, `Site`, `DeviceRole`, or `RackRole` in your **Golden Config Setting** definition in all of `Backup Path`, `Intended Path`, and `Template Path`. 
5. Remove any `dispatcher_mapping` settings you have in your `nautobot_config.py` settings, see Golden Config for alternative options.
6. Update your datasources to use Nautobot Secrets.

!!! warning
    Before you start, please note the `nautobot-server populate_platform_network_driver` command **must be ran in Nautobot 1.6.2 -> 1.6.X** as it will not work once on Nautobot 2.0.

These steps may have little or large impact of change with your environment and potentially (though unlikely), you will not have to make any changes to your environment, to perform the upgrade specifically to continue to support of Golden Config. To help guide you, there is a detailed explanation and question to ask yourself if these changes will effect you or not.

TODO: Insert note about slug and model removals

## Platform Network Driver

!!! info
    You can safely skip this section if you already have your `Platform.network_driver` set and were not using either `platform_slug_map` nor `dispatcher_mapping` settings.

The `Platform.slug` has been replace by Nautobot's `Platform.network_driver`. The nice thing about this feature is it provides mappings to all of the major network library (or frameworks) such as Netmiko and NAPALM to properly map between the slightly different names each library provides, such as `cisco_ios` vs `ios`. However, that means that you must now provide the network_driver on the the Platform object.

While still on the a Nautobot 1.6 instance, run the command `nautobot-server populate_platform_network_driver`, this will help map all of your `Platform.slug`'s to `Platform.network_driver`. If there are any Platform's missed, you most go in and update the Platforms that will be used by Nautobot Plugin Nornir.

If previously you have leveraged the `platform_slug_map` you likely only have to assign the `network_driver` to your multiple current platforms. In the unlikely chance that you have a requirement to override the default network_driver_mappings, you can do so with the [NETWORK_DRIVERS](https://docs.nautobot.com/projects/core/en/stable/user-guide/administration/configuration/optional-settings/?h=network_driver#network_drivers) settings via UI with the [constance settings](https://docs.nautobot.com/projects/core/en/stable/development/apps/api/database-backend-config/).

If previously you have leveraged the `dispatcher_mapping` to use your preferred network library or framework such as Netmiko or NAPALM, you can how use the [framework settings](https://todo/update/me) settings via UI with the [constance settings](https://docs.nautobot.com/projects/core/en/stable/development/apps/api/database-backend-config/).

!!! info
    If you were using the `dispatcher_mapping` for other reasons, see the section below for Custom Dispatcher.

## Dynamic Group

!!! info
    You can safely skip this section if your Dynamic Groups did not use slugs or one of the removed models or you Dynamic Groups are currently in the required state.

In an effort to guide you along, you are highly encouraged to leverage the `nautobot-server audit_dynamic_groups` as [documented](https://docs.nautobot.com/projects/core/en/v2.0.0-rc.3/user-guide/administration/tools/nautobot-server/#audit_dynamic_groups). You will know you have completed this step, when the scope of devices in your Dynamic Group match your expectations.

## GraphQL

!!! info
    You can safely skip this section if your GraphQL did not use slugs or one of the removed models or your saved GraphQL currently renders to the appropriate state.

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

## Golden Config Settings

!!! info
    You can safely skip this section if you are not using slug or one of the Models in your `Backup Path`, `Intended Path`, and `Template Path` settings.


## Custom Dispatcher

!!! info
    You can safely skip this section if you have not been using `dispatcher_mapping` settings.


## Secrets

!!! info
    You can safely skip this section if you have already been using Nautobot Secrets vs Git Repository Token.