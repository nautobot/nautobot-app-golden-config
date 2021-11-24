# Intended Configuration

## Configuration Generation

The Golden Config plugin **Intended Configuration** job generates intended state files for each device in the plugin's configured scope. An intended state file contains the output from rendering the device's Source of Truth Aggregation values through the Jinja templates used by the plugin.

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

## Starting a Intended Configuration Job

To start a intended configuration job manually:

1. Navigate to the Plugin Home (Plugins->Home), with Home being in the `Golden Configuration` section
2. Select _Execute_ on the upper right buttons, then _Intended_
3. Fill in the data that you wish to have configurations generated for up
4. Select _Run Job_

## Intended Configuration Settings

In order to generate the intended configurations at least two repositories are needed.

1. At least one repository in which to save [intended configurations](./navigating-golden.md#git-settings) once generated.
2. At least one repository in which to store device [backups](./navigating-golden.md#git-settings); the device's current operating configuration.
3. The [intended_path_template](./navigating-golden.md#application-settings) configuration parameter.
4. The [jinja_path_template](./navigating-golden.md#application-settings) configuration parameter.

## Data

The data provided while rendering the configuration of a device is described in the [SoT Aggregation](./navigating-sot-agg.md) overview. 
