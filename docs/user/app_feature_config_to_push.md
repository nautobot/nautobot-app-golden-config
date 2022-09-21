# Configuration to Push

!!! note 
    current implementation **only renders the configuration to push, it doesn't actually update the configuration** in the target devices.

The Intended Configuration Job doesn't produce a final configuration artifact ready to use to update a network device. You should understand it as the "intended" **running** configuration, because the intended configuration job attempts to generate what is in the final running configuration, and not the configuration artifact that generates the running configuration.

Aside of enabling the "compliance" feature, there are some other limitations on the intended configuration:

- Because the intended configuration is stored in the Database, and in an external Git repository, it SHOULD NOT contain any secret (or derivative).
- The format of the running configuration is not always the same as the configuration to push in some devices, examples include:
  - Pushing snmpv3 configurations
  - VTP configurations
  - Implicit configurations like a "no shutdown" on an interface

However, Golden Config following intends to become an all encompassing configuration management application, is providing an advanced feature to render the intended configuration in the final format your device is expecting to.

In the UI `Device` detail view, and in the API endpoint `config-to-push`, you can obtain the final configuration artifacts for the devices.

## Customize the processing of the configuration to push process

In the Golden Plugin configuration, you have two options to modify the behavior of the `get_config_to_push`:

- `config_push_callable`: is a list of methods that could be chained, in a specific order, to modify the intended configuration. Check the development guide to know how to create new methods.
- `config_push_subscribed`: is a list of methods names (strings) that define their order in the processing chain. It could reference to your custom callables included in `config_push_callable`, or the default ones available (see next section). This will become the default in your environment, but could be overwritten if needed.

## Existing functions to transform intended configuration

Current available methods:

- **render_secrets**: enables rendering secrets from its `Secrets Group` slug. You need permissions to access these secrets.

### Render Secrets

The `render_secrets` function does an extra render of the original intended configuration, adding support for custom Jinja filters:

- `get_secret_by_secret_group_slug`

> Other default Django or Netutils filters are not available in this Jinja environment. Only `encrypt_type5` and `encrypt_type7` can be used together with the `get_secret` filters.

Because this render happens not in the first one to generate the intended configuration, but on a second one, you must use the `{% raw %}` Jinja syntax to avoid being processed on the first one.

1. For example, an original template like this, `{% raw %}ppp pap sent-username {{ secrets_group["slug"] | get_secret_by_secret_group_slug("username")}}{% endraw %}`
2. Produces an intended configuration as `ppp pap sent-username {{ secrets_group["slug"] | get_secret_by_secret_group_slug("username") }}`
3. After the `render_secrets`, it will become `ppp pap sent-username my_username`.

Notice that the `get_secret` filters takes arguments. In the example, the `Secret_group` slug is passed, together with the type of the `Secret`. Check every signature for more customization.

> Remember that to render these secrets, the user requesting it via UI or API should have read permission to these secret groups.
