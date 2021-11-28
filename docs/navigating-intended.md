# Intended Configuration

## Configuration Generation

The Golden Config plugin provides the ability to generate configurations. The process is a Nornir play that points to a single Jinja template per 
device that generates the configurations. Data is provided via the Source of Truth aggregation and is currently a hard requirement to be turned on if 
generating configuration via the Golden Config plugin. Whatever data is returned by the Source of Truth Aggregation is available to the Jinja template.

As previous stated, there can only be a single template per device. It is often advantageous to break configurations into smaller snippets. A common pattern 
to overcome is:

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

## Adding Jinja2 Filters to the Environment.

This plugin follows [Nautobot](https://nautobot.readthedocs.io/en/stable/plugins/development/#including-jinja2-filters)
in relying on [django_jinja](https://niwinz.github.io/django-jinja/latest/) for customizing the Jinja2 Environment.
Currently, only filters in the django_jinja Environment are passed along to
the Jinja2 Template Environment used by Nornir to render the config template.

### Adding Filters In Nautobot Config

Nautobot documents using the `@django_jinja.library.filter` decorator to register functions as filters with django_jinja.
However, users of plugins are not able to define plugins in the specified jinja2 filter file that is loaded into the Jinja2 Environment.
There are several alternative ways to have functions registered as filters in the django_jinja environment;
below demonstrates defining decorated functions in a separate file, and then importing them in the `nautobot_config.py` file.
This method requires that the file is in a path that is available to Nautobot's python environment.

> django_jinja documents adding filters in the `TEMPLATES` config section;
> since Nautobot sets the `TEMPLATES` config section and does not document this in optional settings,
> it is recommended to only use the `@django_jinja.library.filter` decorator.

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

1. Navigate to the Plugin Home (Plugins->Home), with Home being in the `Golden Configuration` section
2. Select _Execute_ on the upper right buttons, then _Intended_
3. Fill in the data that you wish to have configurations generated for up
4. Select _Run Job_

## Intended Configuration Settings

In order to generate the intended configurations two repositories are needed.

1. A repo to save [intended configurations](./navigating-golden.md#git-settings) to once generated.
2. A repo that stores [backups](./navigating-golden.md#git-settings) used to as the actual configurations.
3. The [intended_path_template](./navigating-golden.md#application-settings) configuration parameter.
4. The [jinja_path_template](./navigating-golden.md#application-settings) configuration parameter.

## Data

The data provided while rendering the configuration of a device is described in the [SoT Aggregation](./navigating-sot-agg.md) overview. 
