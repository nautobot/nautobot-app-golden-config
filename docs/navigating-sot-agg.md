# SoT Aggregation Overview 

The Source of Truth Aggregation feature uses several key components:

* A GraphQL query, per settings instance, which aggregates device data.
* A facility to modify data with a "transposer" function.
* Nautobot's config context feature and policy engine.
* Nautobot's native git platform.

## GraphQL

There is currently support to make an arbitrary GraphQL query that has "device_id" as a variable. It is likely best to use the GraphiQL interface to model
your data, and then save that query as the Saved Query object. The application configuration ensures the following component.

* The query starts with exactly "query ($device_id: ID!)"". This is to help fail fast and help with overall user experience of clear expectations.

> NOTE: The above validation will not happen if the query in the Saved Query object is modified after it's been assigned to the Settings object. That is, validation of the SoTAgg field only happens when the Settings object is created or updated.

Note that the GraphQL query returned is modified to remove the root key of `device`, so instead of all data being within device, such as
`{"device": {"site": {"slug": "jcy"}}}`, it is simply `{"site": {"slug": "jcy"}}` as an example.

It is helpful to make adjustments to the query, and then view the data from the Plugin's home page and clicking on a given device's `code-json` icon.

## Transposer Function

The transposer function is an optional function to make arbitrary changes to the data after the fact. There is a Plugin configuration that allows the
operator to point to a function within the python path by a string. The function will receive a single variable, that by convention should be called
`data`. The function should return a valid Python json serializable data structure.

```python
def transposer(data):
    """Some."""
    if data["platform"]["slug"] == "cisco_ios":
        data["platform"].update({"support-number": "1-800-ciscohelp"})
    if data["platform"]["slug"] == "arista_eos":
        data["platform"].update({"support-number": "1-800-aristahelp"})
    return data
```

While the example transposer is silly and untested, it provides the structure for which a transposer can be used. The possibilities are obviously endless,
such as reaching out to an external system, but operators should use caution not to overload complexity into the transposer. 

The configuration required in the Plugin configuration is as described below.

```python
PLUGINS_CONFIG["nautobot_golden_config"]["sot_agg_transposer"] = "nautobot_golden_config.transposer.transposer"
```
The path described must be within the Python path of your worker. It is up to the operator to ensure that happens.

## Config Contexts

While outside the scope of this document, it is worth mentioning the power that the `config_context` feature, along with integration to Git, can provide in this
solution. Config contexts can be used for arbitrary JSON serializable data structures. That is helpful to model configuration
that would not normally be available within Nautobot Core Django ORM models or within a Nautobot plugin's custom models. A common use case is to model "global configuration" like data, such as NTP, DNS, SNMP, etc.
For more information, please refer to the Nautobot Core documentation on
[Config Contexts](https://nautobot.readthedocs.io/en/latest/additional-features/config-contexts/#configuration-contexts) and leveraging
[Git Data Sources](https://nautobot.readthedocs.io/en/stable/user-guides/git-data-source/#using-git-data-sources).

## Performance

The GraphQL and transposer functions have potential to seriously impact the performance of the Nautobot application. Operator should weigh the pros and cons of the solution before committing to the use of these functions.

## Sample Query

To test your query in the GraphiQL UI, obtain a device's uuid, which can be seen in the url of the detailed device view. Once you have a valid device uuid, you can use the "Query Variables" portion of the UI, which is on the bottom left-hand side of the screen.

Example: Query Variables
```
{
  "device_id": "c2dfa612-3c6b-4a67-8492-a7ca346641f9"
}
```

GraphQL may be new to many users, and while the GraphiQL interface is great way to get started, the following query is for reference. It is
highly recommended to alias name (as in `hostname: name` shown below), as there will be a namespace issue with nornir tasks, which often
take in name as a parameter. 

```
query ($device_id: ID!) {
  device(id: $device_id) {
    config_context
    hostname: name
    position
    serial
    primary_ip4 {
      id
      primary_ip4_for {
        id
        name
      }
    }
    tenant {
      name
    }
    tags {
      name
      slug
    }
    device_role {
      name
    }
    platform {
      name
      slug
      manufacturer {
        name
      }
      napalm_driver
    }
    site {
      name
      slug
      vlans {
        id
        name
        vid
      }
      vlan_groups {
        id
      }
    }
    interfaces {
      description
      mac_address
      enabled
      name
      ip_addresses {
        address
        tags {
          id
        }
      }
      connected_circuit_termination {
        circuit {
          cid
          commit_rate
          provider {
            name
          }
        }
      }
      tagged_vlans {
        id
      }
      untagged_vlan {
        id
      }
      cable {
        termination_a_type
        status {
          name
        }
        color
      }
      tagged_vlans {
        site {
          name
        }
        id
      }
      tags {
        id
      }
    }
  }
}
```