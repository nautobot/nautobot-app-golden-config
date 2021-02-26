# Configuration Compliance 

The following should be noted by what is meant by configuration compliance. Configurations are considered to be compliant if the generated configuration 
(generally by merging data and Jinja2, will be referred to as the intended configuration from hence forth) matches "exactly" as the actual configuration is 
on the backup. This may confusing to some, as for example to the average network engineer, there is no difference between `int g0/0` and
`interface GigabitEthernet0/0` but for the purpose of configuration compliance, it is not a match... full stop.

It's helpful to understand what are some common reasons a device is not compliant.

* There is missing configuration on the device.
* There is extra configuration on the device.
* The data used to generate the configuration is incorrect, and created a "false positive".
* The template used to generate the configuration is incorrect, and created a "false positive".
* The parser used to obtain the configuration from the feature is incorrect, and created a "false positive".

There is no magic to determine the state of configuration. You still must define what is good configuration and compare it. There are several reasons why 
configuration may be as a network engineer wants it, but the tool correctly considers it non-compliant, since the tool is only comparing two configurations.
The tool makes no assumptions to determine what an engineer may want to do, but did not document via the configuration generation process.

## Installation Instructions



## Configuration Compliance Parsing Engine

Configuration compliance is different then a simple unix diff. While the UI provides both, the compliance metrics are not influenced by the unix diff 
capabilities. One of the challenges of getting a device into compliance is the ramp up it takes to model and generate configurations for an entire 
configuration. The compliance engine has several features to better build out this process.

1. The ability to parse into smaller sections, given a list of root configuration elements.
2. The ability to consider ordered and non-ordered configurations.
3. The ability to dynamically understand parent/child relationships within the configurations.

In regards to `1`, consider the following example of how to obtain service configurations:
```
service
no service
```
Specific configurations that start with either of these commands can be grouped together.

In regards to `2`, consider the configurations of SNMP on a nexus switch. 
```
snmp-server community secure group network-admin
snmp-server community networktocode group network-operator
```

The above configurations are rendered based on the order in which they were entered, not based on the a deterministic way. The comparison process takes this into consideration. 

In regards to `3`, consider the following example of BGP configuration. 
```
router bgp
prefix-list
```
All configurations that are a parent and child relationships would be considered within the parsing engine. Additionally, if one configuration line was 
wrong, only that line and the parents would be shown, not all lines or only the missing configuration without context of the parents, e.g. Given:

Actual
```
router bgp 65250
  router-id 10.0.10.5
  log-neighbor-changes
  address-family ipv4 unicast
    redistribute direct route-map PERMIT_CONN_ROUTES
  neighbor 10.10.10.5
    remote-as 65250
    address-family ipv4 unicast
```

Intended
```
router bgp 65250
  router-id 10.0.10.6
  log-neighbor-changes
  address-family ipv4 unicast
    redistribute direct route-map PERMIT_CONN_ROUTES
  neighbor 10.10.10.5
    remote-as 65250
    address-family ipv4 unicast
```
Would result in the identfying the missing configurations as:

```
router bgp 65250
  router-id 10.0.10.6
```

### Configuration Compliance Settings

Configuration compliance requires the Git Repo settings for `config backups` and `intended configs`--which are covered in their respective sections--regardless if they are actually managed via the plugin or not.

The Configuration compliance feature map must be created per the operator. 

TODO: Once move the UI, document for now an example can be found [here](https://github.com/networktocode-llc/nautobot-gc-data/blob/be82d7f686a573ad33f85b2313e632d9bc2e7910/config_contexts/all.yml#L7-L196)


# Usage

There is a single process and several views that the plugin provides.

## Plugins Buttons

The plugins buttons provides you the ability to navigate to Run the script, overview report, and detailed report.

## Run Script

This can be accessed via the Plugins drop-down via `Run Script` button, it will immediately run the script once the it starts.


## Detail Report

This can be accessed via the Plugins drop-down via `Compliance` details button. From there you can filter the devices via the form on the right side, limit the columns with the `Configure` button, or 
bulk delete with the `Delete` button. Additionally each device is click-able to view the details of that individual device. 

You can configure the columns to limit how much is showing on one screen.

## Device Details

You can get to the device details form either the Compliance details page, or there is a `content_template` on the device model page is Nautobot's core instance (more details later.)


## Overview Report

There is a global overview or executive summary that provides a high level snapshot of the compliance. There are 3 points of data captured.

* Devices - This is only compliant if there is not a single non-compliant feature on the device. So if there is 10 features, and 1 feature is not compliant, the device is considered non-compliant.
* Features - This is the total number of features for all devices, and how many are compliant, and how many are non-compliant.
* Per Feature - This is a breakdown of that feature and how many within that feature are compliant of not.

## Device Template Content

The plugin makes use of template content `right_page` in order to use display in-line the status of that device in the traditional Nautobot view. From here you can click the link to see the
detail compliance view.


## Site Template Content

The plugin makes use of template content `right_page` in order to use display in-line the status of that entire site in the traditional Nautobot view. 
