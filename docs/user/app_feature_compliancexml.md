# Navigating Compliance Using XML

XML based compliance provides a mechanism to understand device configurations stored in XML format and compare between them.

## Defining Compliance Rules

Compliance rules are defined as XML `config-type`.

The `config to match` field is used to specify an XPath query. This query is used to select specific nodes in the XML configurations for comparison. If the `config to match` field is left blank, all nodes in the configurations will be compared.

### XPath in Config to Match

XPath (XML Path Language) is a query language for selecting nodes from an XML document. In our application, XPath is used in the `config to match` field to specify which parts of the device configurations should be compared.

Here are some examples of XPath queries that can be used in the `config to match` field:

![Example XML Compliance Rules](../images/compliance-rule-xml.png)

## Device Config Compliance View

![Config Compliance Device View](../images/device-compliance-xml.png)

### Diff Output

The diff output shows the differences between the device configurations. Each line in the diff output represents a node in the XML configurations. The node is identified by its XPath, and the value of the node is shown after the comma.

Here's a sample diff output:

```
/config/system/aaa/user[1]/password[1], foo
/config/system/aaa/user[1]/role[1], admin
/config/system/aaa/radius/server[1]/host[1], 1.1.1.1
/config/system/aaa/radius/server[1]/secret[1], foopass
/config/system/aaa/radius/server[2]/host[1], 2.2.2.2
/config/system/aaa/radius/server[2]/secret[1], bazpass
```
