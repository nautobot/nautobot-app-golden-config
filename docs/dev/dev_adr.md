# Architecture Decision Records

The intention is to document deviations from a standard Model View Controller (MVC) design.

## Pivoting Compliance View

The view that was preferred for compliance would be devices on y-axis but the features on the x-axis. However, the x-axis (features) cannot be known when building the Django model. The model ends up looking like:

| Device   | feature | Compliance |
| -------- | ------- | ---------- |
| nyc-rt01 | aaa     | True       |
| nyc-rt01 | ntp     | False      |
| nyc-rt01 | dns     | False      |
| nyc-rt02 | aaa     | True       |
| nyc-rt02 | dns     | False      |

The expected view required expected is something like:

| Device   | aaa   | dns   | ntp   |
| -------- | ----- | ----- | ----- |
| nyc-rt01 | True  | False | False |
| nyc-rt02 | True  |       | False |

In order to accommodate this, `django-pivot` is used, which greatly simplifies building the query. However, `django-pivot` requires the ability to "count" vs a boolean. Because of that, there is a "shadow" field created that sets to 0 if False, and 1 if True. This is enforced on the `save` method of the `ConfigCompliance` model.

## Compliance View

Important to understand `Pivoting Compliance View` first. There is additional context for how to handle bulk deletes. The logic is to find all of the `ConfigCompliance` data, given a set of `Device` objects. 

Additionally, this makes use of the `alter_queryset` method, as at start time of the application all features are not necessarily set and needs to be a runtime query that sets the x and y axis correctly.

The absence of data, meaning, a device that is does not have a feature, is the equivalent of a None.

## Dynamic Application Features

There are features within the application that can be turned on/off for backup, compliance, and intended. When they are toggled, this will update what is shown in:

* Navigation
* Jobs
* Data Sources
* Tables
* Template Contents

This is generally handled with a pattern similar to:

```python
jobs = []
if ENABLE_BACKUP:
    jobs.append(BackupJob)
if ENABLE_INTENDED:
    jobs.append(IntendedJob)
if ENABLE_COMPLIANCE:
    jobs.append(ComplianceJob)
jobs.extend([AllGoldenConfig, AllDevicesGoldenConfig])
```

## Home View

The Home view is generally based on the model `GoldenConfig`, however, in reality the view that shows up is based on the core `Device` model. This is because, when a device is included in the Dynamic Group, this does not mean that there is an entry in `GoldenConfig` yet. So there is nothing to see yet, such as the ability to click and run job on a device. It was confusing to users as to what was shown in the view vs what is in scope currently.

This complicates things such that the view data is one level nested, from the Model. Meaning, the query is based on `Device`, but the data is primarily in `GoldenConfig`. Do accommodate, there is an annotated query, similar to:

```python
        return self.queryset.filter(id__in=qs).annotate(
            backup_config=F("goldenconfig__backup_config"),
            intended_config=F("goldenconfig__intended_config"),
```

This allows the tables to be a bit simpler as the data is directly accessible without traversing the foreign key.

## Home Tables

There is not a one-to-one for fields to data shown. There is custom logic that sees if the last ran date is the same as last successful data and renders either green or red. Here is an example of the code that is actually rendered (logic is within `_render_last_success_date` method):

```python
    def render_backup_last_success_date(self, record, column):
        """Pull back backup last success per row record."""
        return self._render_last_success_date(record, column, "backup")
```

## Filtering Logic

The filtering logic happens in the `get_job_filter` function. Any consumer (job/view/etc) should use this to ensure everything is filtered in the same way.

## Diff logic

There is a function mapper for the diff logic. This allows for the diff logic to take on different proccesses for cli, json, and custom. This is enforced on the save method of `ConfigCompliance`.

## Dynamic Group

There was originally a `scope` associated with the project, this was changed to a Dynamic Group to make use of the features within Core. There is backwards compatibility for the time being. 

## Management Commands

There is specific management commands to run the jobs associated with the project. In a future version, they will reference the management commands in core. 

## SoT Aggregation 

There is a custom SoT Aggregation method, originally this pre-dated Nautobot Core having saved queries and was a way to handle to have a saved query. Currently, it allows operators to transform data by providing a function to post process that data. This functionality is handled to code similar to:

```python
    if PLUGIN_CFG.get("sot_agg_transposer"):
        try:
            data = import_string(PLUGIN_CFG.get("sot_agg_transposer"))(data)
        except Exception as error:
            return (400, {"error": str(error)})
```

## Git Actions

The data source contract is used for reading from Git, but extended for pushing to Git. 