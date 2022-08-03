# Intended Configuration

## Configuration Generation

The Golden Config plugin **Intended Configuration** job generates intended state files for each device in the plugin setting's configured scope. An intended state file contains the output from rendering the device's Source of Truth Aggregation values through the Jinja templates used by the plugin.

The job itself is a Nornir play which uses a single Jinja template per device. Source of Truth Aggregation data comes from the GraphQL query configured in the Golden Config plugin's settings. An important component of the SoT Aggregation data are the `config_context` values. `config_context` should contain a vendor-neutral, JSON structured representation of a device's configuration values: a list of NTP/AAA/Syslog servers, common VRFs, etc. See [Config Contexts](https://nautobot.readthedocs.io/en/latest/additional-features/config-contexts/#configuration-contexts) for more information.

The Source of Truth Aggregation feature of the plugin must be enabled for the plugin to generate intended configuration state output.

There can only be a single Jinja template per device. Device configurations can become daunting to create via a Jinja template, if you try to place all of the logic for a device's configuration inside a single Jinja2 file. These template files can quickly become too complex to maintain. So, it is often advantageous to break configurations into smaller feature-oriented snippets, each contained in their own discrete template file. Operators often keep their main, top-level, template simple and easy to maintain by only placing include statements in it:

```jinja
!
{% include os ~ '/services.j2' %}
!
{% include os ~ '/hostname.j2' %}
!
{% include os ~ '/ntp.j2' %}
!
```
or

```jinja
!
{% set features = ['services', 'hostname', 'ntp'] %}
{% for feature in features %}
{% include os ~ '/' ~ feature ~ '.j2' %}
!
{% endfor %}
```

In these examples, `/services.j2`, `/ntp.j2`, etc. could contain the actual Jinja code which renders the configuration for their corresponding features. Alternately, in more complex environments, these files could themselves contain only include statements in order to create a hierarchy of template files so as to keep each individual file neat and simple. Think of the main, top-level, template as an entrypoint into a hierarchy of templates. A well thought out structure to your templates is necessary to avoid the temptation to place all logic into a small number of templates. Like any code, Jinja2 functions become harder to manage, more buggy, and more fragile as you add complexity, so any thing which you can do to keep them simple will help your automation efforts.

## Adding Jinja2 Filters to the Environment.

This plugin follows [Nautobot](https://nautobot.readthedocs.io/en/stable/plugins/development/#including-jinja2-filters) in relying on [django_jinja](https://niwinz.github.io/django-jinja/latest/) for customizing the Jinja2 Environment. Currently, only filters in the `django_jinja` Environment are passed along to the Jinja2 Template Environment used by Nornir to render the config template.

### Adding Filters In Nautobot Config

Nautobot documents using the `@django_jinja.library.filter` decorator to register functions as filters with `django_jinja`. However, users of plugins are not able to define plugins in the specified jinja2 filter file that is loaded into the Jinja2 Environment.

There are several alternative ways to have functions registered as filters in the `django_jinja` environment; below demonstrates defining decorated functions in a separate file, and then importing them in the `nautobot_config.py` file. This method requires that the file is in a path that is available to Nautobot's python environment.

!!! note
    `django_jinja` documents adding filters in the `TEMPLATES` config section;
    since Nautobot sets the `TEMPLATES` config section and does not document this in optional settings,
    it is recommended to only use the `@django_jinja.library.filter` decorator.

#### custom_jinja_filters/config_templates.py

```python
import ipaddress

from django_jinja import library


@library.filter
def get_hostmask(address):
    ip_address = ipaddress.ip_network(address)
    return str(ip_address.hostmask)


@library.filter
def get_netmask(address):
    ip_address = ipaddress.ip_network(address)
    return str(ip_address.netmask)
```

#### nautobot_config.py

```python
...
# custom_jinja_filters must be in nautobot's python path
from custom_jinja_filters import config_templates
...
```

## Starting a Intended Configuration Job

To start a intended configuration job manually:

1. Navigate to `Golden Config -> Home`, with Home being in the `Golden Configuration` section
2. Select _Execute_ on the upper right buttons, then _Intended_
3. Fill in the data that you wish to have configurations generated for up
4. Select _Run Job_

## Intended Configuration Settings

In order to generate the intended configurations at least two repositories are needed.

1. At least one repository in which to save [intended configurations](./app_use_cases.md#git-settings) once generated.
2. At least one repository in which to store device [backups](./app_use_cases.md#git-settings); the device's current operating configuration.
3. The [intended_path_template](./app_use_cases.md#application-settings) configuration parameter.
4. The [jinja_path_template](./app_use_cases.md#application-settings) configuration parameter.

### Intended Repository Matching Rule

!!! note
    Only use a Intended Repository Matching Rule if you have **more than one** intended repository. It is **not needed"" if you only have one repository. The operator is expected to ensure that every device results in a successful matching rule (or that device will fail to render a config).

The `intended_match_rule` setting allows you to match a given `Device` Django ORM object to a backup Git repository. This field should contain a Jinja2-formatted template. The plugin populates the variables in the Jinja2 template via the GraphQL query configured on the plugin.

This is exactly the same concept as described in [Backup Repository Matching Rule](./app_feature_backup.md#repository-matching-rule), and better described there.

## Data

The data provided while rendering the configuration of a device is described in the [SoT Aggregation](./app_feature_sotagg.md) overview.
