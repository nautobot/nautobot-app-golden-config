# Navigating Compliance Using Structured Data

JSON based compliance provides a mechanism to understand device configurations stored in JSON format and compare between them. There are two variants offered natively.

- JSON_DEEPDIFF - Uses [Deepdiff](https://zepworks.com/deepdiff/current/) and provides a basic root path view in the compliance results.
- JSON_JDIFF - Uses [jdiff](https://jdiff.readthedocs.io/en/latest/) and provides a more sophisticated diff'ing capability to simplify the compliance results.

## Caveats
- The `Compliance Rule` need to be defined as JSON_DEEPDIFF or JSON_JDIFF `config-type`.
- When creating `Compliance Rules` with the config type of either variant of JSON, the `config to match` field is used to specify individual top-level JSON keys, or it can be left blank to compare all keys.
- Uses Git repositories for backup and intended configurations.

## Quick Start Guide JSON (Deepdiff)

1. First, the compliance feature needs to be created, the feature name needs to be unique for a Platform and can not be shared between CLI and JSON types.

    ![Example Feature Creation](../images/01-navigating-compliance-json-deepdiff.png#only-light)
    ![Example Feature Creation](../images/01-navigating-compliance-json-deepdiff-dark.png#only-dark)

2. Link the feature that was just created to a rule definition.

    ![Example Rule Creation](../images/02-navigating-compliance-json-deepdiff.png#only-light)
    ![Example Rule Creation](../images/02-navigating-compliance-json-deepdiff-dark.png#only-dark)

3. Now that the definitions are created and the rule is created and mapped to a Platform, execute compliance job under Jobs.

4. Verify the compliance results

In the navigation menu: `Golden Config -> Configuration Compliance`.

![Example Compliance Run in UI](../images/03-navigating-compliance-json-deepdiff.png#only-light)
![Example Compliance Run in UI](../images/03-navigating-compliance-json-deepdiff-dark.png#only-dark)

Example of a Non-Compliant rule:

![Example Non-Compliant Run in UI Detail](../images/04-navigating-compliance-json-deepdiff.png#only-light)
![Example Non-Compliant Run in UI Detail](../images/04-navigating-compliance-json-deepdiff-dark.png#only-dark)

## Quick Start Guide JSON (jdiff)

1. First, the compliance feature needs to be created, the feature name needs to be unique for a Platform and can not be shared between CLI and JSON types.

![Example Feature Creation](../images/01-navigating-compliance-json-jdiff.png#only-light)
![Example Feature Creation](../images/01-navigating-compliance-json-jdiff-dark.png#only-dark)

2. Link the feature that was just created to a rule definition.

![Example Rule Creation](../images/02-navigating-compliance-json-jdiff.png#only-light)
![Example Rule Creation](../images/02-navigating-compliance-json-jdiff-dark.png#only-dark)

3. Now that the definitions are created and the rule is created and mapped to a Platform, execute compliance job under Jobs.

4. Verify the compliance results

In the navigation menu: `Golden Config -> Configuration Compliance`.

![Example Compliance Run in UI](../images/03-navigating-compliance-json-jdiff.png#only-light)
![Example Compliance Run in UI](../images/03-navigating-compliance-json-jdiff-dark.png#only-dark)

Example of a Non-Compliant rule:

![Example Compliance Run in UI Detail](../images/04-navigating-compliance-json-jdiff.png#only-light)
![Example Compliance Run in UI Detail](../images/04-navigating-compliance-json-jdiff-dark.png#only-dark)


!!! info
    If a side by side diff is preferred you can navigate to `Golden Config -> Configuration Compliance` and find the device you're looking at.  Finally, click on the `document` icon.

Seeing the diff button alone will **only** show up for devices using JSON compliance rules.

![Example of Diff Icon](../images/navigating-compliance-json.png#only-light)
![Example of Diff Icon](../images/navigating-compliance-json-dark.png#only-dark)

The detailed diff view will show a side by side diff, this looks the same as the CLI view.
