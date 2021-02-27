# Golden Configuration 

An navigation overview of the entire plugin.

# Home

The Home view is a portal to understand what the status of the devices are. 

![Home Overview](./img/golden-overview.png)

Some of the information descibed in this view, may not be immediately obvious.

* The Backup/Intended/Compliance status will always show the last time the job was successfully ran for that device, but there are several conditions it may be in.
  * Green with a date states that the ran was successful, which was the last time the job ran. 
  * Red with a data indicates the last time the job ran successfully, with the last time the job was attempted in be shown when you mouse over the date.
  * A red double-dashed icon indicated the job has never been successful
* The icons are provided in the following order, that largely matches the status.
  * Backups
  * Intended
  * Unix Diff
  * SoT aggregation data
  * Run job

The first four bring up a "modal" or "dialogue box" which has a detailed view for a dedicated page. The run job brings the user to a job to run all three 
componets against all of the devices.

# Jobs

There are a series of Jobs that are registed via the Plugin. They can be viewed from the standard Jobs view.

![Job Overview](./img/job-overview.png)

Each Job attempts to provide sane error handling, and respects the `debug` flag to provide more information.

![Job Result](./img/job-result.png)

# Application Settings

The golden configuration plugin settings can be found by navigating to `Plugins -> Compliance Rules -> Settings` button..

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
> Note: Each of these will be further detailed in their respective sections.

# Plugins Buttons

The plugins buttons provides you the ability to navigate to Run the script, overview report, and detailed report.

# Run Script

This can be accessed via the Plugins drop-down via `Run Script` button of the `Home` view, the user will be provided a form of the Job (as described 
above), which will allow the user to limit the scope of the request.

# Device Template Content

The plugin makes use of template content `right_page` in order to use display in-line the status of that device in the traditional Nautobot view. From here you can click the link to see the detail compliance view.

# Site Template Content

The plugin makes use of template content `right_page` in order to use display in-line the status of that entire site in the traditional Nautobot view. 

## API

There is no way to currently run the script via an API, this would be helpful to use in the configuration compliance workflow, and will be a future feature.