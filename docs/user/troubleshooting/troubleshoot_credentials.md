# Troubleshooting Credentials

Credentials are an important aspect of the Golden Config application. In order to capture backup configs the application must have credentials to login to network devices. Golden Config simply utilizes another library to generate the inventory and to populate the credentials to use.

At the time of writing this there are three main credentials types that Golden Config can utilize.

- Environment Variables
- Configuration Settings Variables
- Nautobot Integrated Secrets Group Functionality

These are documented in the [Nautobot Plugin Nornir](https://docs.nautobot.com/projects/plugin-nornir/en/latest/user/app_feature_credentials/) documentation.

### No Username/Password Preemptively Failed

This will cover some things to check for each of the credentials classes supported.

- Environment Variables
    - Make sure the `PLUGIN_CONFIG` is correct and the credentials class is not typo'd.

    ```python
    PLUGINS_CONFIG = {
    "nautobot_plugin_nornir": {
        "nornir_settings": {
           "credentials": "nautobot_plugin_nornir.plugins.credentials.env_vars.CredentialsEnvVars"
            },
        }
    }
    ```

    - Make sure the the three environment variables are defined and accessible in the worker node.
        - NAPALM_USERNAME
        - NAPALM_PASSWORD
        - DEVICE_SECRET

- Configuration Settings Variables
    - Make sure the `PLUGIN_CONFIG` is correct and the credentials class is not typo'd.

    ```python
    PLUGINS_CONFIG = {
        "nautobot_plugin_nornir": {
            "nornir_settings": {
                "credentials": "nautobot_plugin_nornir.plugins.credentials.settings_vars.CredentialsSettingsVars",
            },
            "username": "ntc",
            "password": "password123",
            "secret": "password123",
        }
    }
    ```

    !!! info
        A common pattern is to have these username/password/secrets reference "other" environment variables using the `os.getenv()` python function. This is fine, but the environment variables **MUST** be resolvable from within the workers environment.

- Nautobot Integrated Secrets Group Functionality

    This credentials class uses the Nautobot core functionality for [secrets/secret_groups](https://docs.nautobot.com/projects/core/en/stable/core-functionality/secrets/). There is some caveats to this feature and some troubleshooting tips are provided below.

    - Make sure the `PLUGIN_CONFIG` is correct and the credentials class is not typo'd.

    ```python
    PLUGINS_CONFIG = {
        "nautobot_plugin_nornir": {
            "nornir_settings": {
                "credentials": "nautobot_plugin_nornir.plugins.credentials.nautobot_secrets.CredentialsNautobotSecrets",
            }
        }
    }
    ```

    - Make sure you have the `secrets` defined and properly linked to environment variables or text file(s).
    - Make sure the `secrets` are assigned to a `secret_group` and that the proper "types" are used.

        !!! warn
            This credentials class is expecting some defaults to be used to auto load the credentials. The below "types" must be used if the default PLUGIN_CONFIG from above is used. If the `Access Type` needs to be changed see [Nautobot Secrets Nornir Docs](https://docs.nautobot.com/projects/plugin-nornir/en/latest/user/app_feature_credentials/#nautobot-secrets).

        - Access Type = "Generic" and Secret_Type = "Username" and linked to the secret objects that links to the username.
        - Access Type = "Generic" and Secret_Type = "Password" and linked to the secret objects that links to the password.
        - Access Type = "Generic" and Secret_Type = "Secret" and linked to the secret objects that links to the secret.

    - Make sure the `secret_group` is applied to the device.
        - Edit device object and save it with a secret_group that identifies the credentials for that device.
