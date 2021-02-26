## Compliance Rules Settings

The golden configuration plugin settings can be found by navigating to `Plugins -> Compliance Rules`.

![Navigate to Compliance Rules](./img/navigate-compliance-rules.png)

To configure the settings click `Settings`.

Next fill out the Settings.

|Setting|Explanation|
|:--|:--|
|Backup Path|This represents the Jinja path where the backup files will be found.  The variable `obj` is availiable as the device instance object of a given device, as is the case for all Jinja templates. e.g. `{{obj.site.slug}}/{{obj.name}}.cfg`|
|Intended Path|The Jinja path representation of where the generated file will be places. e.g. `{{obj.site.slug}}/{{obj.name}}.cfg`|
|Template Path|The Jinja path representation of where the Jinja temaplte can be found. e.g. `{{obj.platform.slug}}.j2`|
|GraphQL Query|A query that is evaluated and used to render the config. The query must start with `query ($device: String!)`.|
|Lines to Remove|Configuration lines to remove that match these patterns, one pattern per line.|
Lines to Substitute|Uses a regex pattern with replacement config three pipes (\|\|\|) and a regex pattern with a capture group. e.g. `redacted_config\|\|\|username\s+\S+\spassword\s+5\s+(\S+)\s+role\s+\S+`|
<br>
> Note: Each of these will be detailed further below.

### Backup Path

### Intended Path

### Template Path

### GraphQL Query

### Lines to Remove

### Lines to Substitute
