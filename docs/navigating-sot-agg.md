# SoT Aggregation Overview 

The Source of Truth Aggregation Overview is driven by a few key components.

* The ability to have a single GraphQL query to aggregate information.
* The ability to modify data with a "transposer" function.
* The usage of config contexts and the nautobot's native git platform.

# GraphQL

There is currently support to make an arbitrary GraphQL query that has "device" as a variable. It is likely best to use the GraphiQL interface to model
your data, and then save it to the configuration. The configuration ensures the following two components.

* The query is a valid GraphQL query.
* The query starts with exactly "query ($device: String!)". This is to help fail fast and help with overall user experience of clear expectations.

Due to the nature of the query, the results by default always return with a nested data structure of `devices[0]{data}`. There is optionally a toggle to 
shorten that to simply `data`. 

It is helpful to make adjustments to the query, and then view the data from the Plugin's home page and clicking on a given device's `code-json` icon.

# Transposer Function

The transposer function is an optional function to make arbitrary changes to the data after the fact. There is a Plugin configuration that allows the
operator to point to a function within the python path by a string. The function will receive a single variable, that by convention should be called
`data`. The function should return a valid Python json serializable data structure.

```python
def transposer(data):
    """Some."""
    if data["devices"][0]["platform"]["slug"] == "cisco_ios":
        data["devices"][0]["platform"].update({"support-number": "1-800-ciscohelp"})
    if data["devices"][0]["platform"]["slug"] == "arista_eos":
        data["devices"][0]["platform"].update({"support-number": "1-800-aristahelp"})
    return data
```

While the example transposer is silly and untested, it provides the structure for which a transposer can be use. The possibilities are obviously endless,
such as reaching out to an external system but operators should use caution not to overload complexity into the transposer. 

The configuration required in the Plugin configuration is as described below.

```python
PLUGINS_CONFIG["nautobot_golden_config"]["sot_agg_transposer"] = "nautobot_golden_config.transposer.transposer"
```
The path described must obviously be within the Python path of your worker. It is up to the operator to ensure that happens.

# Config Context

Outside of the scope of this document, but it is worth mentioning the power that configuration context's with integration to Git can provide in this
solution.

# Performance

The GraphQL and transposer functionality could seriously impact the performance of the server. There are no restrictions imposed as it is up to the
operator to way the pro's and con's of the solution.
