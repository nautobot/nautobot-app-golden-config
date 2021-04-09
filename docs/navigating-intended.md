# Configuration Generation

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

# Intended Configuration Settings

In order to generate the intended configurations two repositories are needed.

1. A repo to save intended configurations to once generated. [See](./navigating-golden.md#git-settings)
2. A repo that stores Jinja2 templates used to generate intended configurations. [See](./navigating-golden.md#git-settings)
3. The [intended_path_template](./navigating-golden.md#application-settings) configuration parameter.
4. The [jinja_path_template](./navigating-golden.md#application-settings) configuration parameter.

# Data

The data provided while rendering the configuration of a device is described in the [SoT Aggregation](./navigating-sot-agg.md) overview. 
