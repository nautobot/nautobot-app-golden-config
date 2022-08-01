# Configuration Compliance 

> Note:
This document provides instructions based on `CLI` based compliance.  The other options are `JSON` [structured data compliance](./app_feature_compliancejson.md) and [custom compliance](./app_feature_compliancecustom.md).

## Configuration Compliance Parsing Engine

Configuration compliance is different than a simple UNIX diff. While the UI provides both, the compliance metrics are not influenced by the UNIX diff 
capabilities. One of the challenges of getting a device into compliance is the ramp up it takes to model and generate configurations for an entire 
configuration. The compliance engine has several features to better build work through this process.

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

The above configurations are rendered based on the order in which they were entered, not based on the a deterministic way. The comparison process takes this into consideration, to ensure that the following is not non-compliant when ordering option is not considered.

```
snmp-server community networktocode group network-operator
snmp-server community secure group network-admin
```

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
Would result in the identifying the missing configurations as:

```
router bgp 65250
  router-id 10.0.10.6
```

> Note: A platform will not run successfully against a device unless at least one compliance rule is set. 

