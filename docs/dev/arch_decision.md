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

| Device   | aaa  | dns   | ntp   |
| -------- | ---- | ----- | ----- |
| nyc-rt01 | True | False | False |
| nyc-rt02 | True |       | False |

In order to accommodate this, `django-pivot` is used, which greatly simplifies building the query. However, `django-pivot` requires the ability to "count" versus a boolean. Because of that, there is a "shadow" field created that is set to 0 if False, and 1 if True. This is enforced on the `save` method of the `ConfigCompliance` model.

## Compliance View

Important to understand `Pivoting Compliance View` first. There is additional context for how to handle bulk deletes. The logic is to find all of the `ConfigCompliance` data, given a set of `Device` objects.

Additionally, this makes use of the `alter_queryset` method, as at start time of the application all features are not necessarily set and needs to be a runtime query that sets the x and y axis correctly.

The absence of data, meaning, a device that is does not have a feature, is the equivalent of a None.

## Dynamic Application Features

There are features within the application that can be turned on/off for backup, compliance, and intended. When they are toggled, this will update what is shown in:

- Navigation
- Jobs
- Data Sources
- Tables
- Template Contents

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

The Home view is generally based on the model `GoldenConfig`; however, in reality the view that shows up is based on the core `Device` model. This is because, when a device is included in the Dynamic Group, this does not mean that there is an entry in `GoldenConfig` yet. So there is nothing to see yet, such as the ability to click and run job on a device. It was confusing to users as to what was shown in the view vs what is in scope currently.

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

There is a function mapper for the diff logic. This allows for the diff logic to take on different processes for cli, json, and custom. This is enforced on the save method of `ConfigCompliance`.

## Dynamic Group

There was originally a `scope` associated with the project, this was changed to a Dynamic Group to make use of the features within Core. There is backwards compatibility until version 2.0.0.

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

## Configuration Postprocessing

Intended configuration generated by Golden Config Intended feature is designed for comparing to the "running" configuration (assuring compliance comparing to the backup configuration). Using the default Intended configuration for remediation/provisioning of a network device configuration is not always possible. For instance, no secrets should be rendered to the Intended configuration, as it is stored in Git/Database, or maybe some reordering of commands is required to create a valid configuration artifact.

The PROCESSING feature, that is enabled as a Dynamic Application Feature, exposes a single device UI and API view to manipulate the Intended configuration available for Golden Config, with extra processing steps. There are some default functions (i.e. `render_secrets`), but those can be expanded, and the order can be changed, via Nautobot configuration settings (`postprocessing_subscribed` and `postprocessing_callables`).

!!! Note
    This configuration generated after postprocessing is not stored either in the Database or in Git.

Both API views, as commented, are only targeting ONE single device because being a synchronous operation (versus the rest of the features that are run asynchronously as Jobs), it could take too much time, and have an undesired impact in Nautobot performance.

All the functions used in the post-processing chain require a consistent signature:
`func(config_postprocessing: str, configs: models.GoldenConfig, request: HttpRequest) -> str`.

- `config_postprocessing: str`: it's the reference configuration to use as template to render.
- `configs: models.GoldenConfig`: it contains reference to other configs (backup) that could be used to create remediation, and it contains the `Device` object to identify the GraphQL information to take from.
- `request: HttpRequest`: it could contain special query params, and for the `render_secrets` one, it contains information about the `User` requesting it, to validate the permissions.

Finally, it always returns the processing from the `config_processing`.

The API view, under the path `config-postprocessing`, uses custom permissions, named `ConfigPushPermissions`, which ensures the user has general permissions for `nautobot_golden_config.view_goldenconfig`, and specific permissions to view the `Device` object requested.

### Renders Secrets

It was decided to restrict the usage of Jinja filters to only the ones related to getting Nautobot secrets values (defined here), plus the `encrypt_<vendor>_type5` and `encrypt__<vendor>_type7` filters from [Netutils](https://netutils.readthedocs.io/en/latest/dev/code_reference/password/#netutils.password). Remember that this function is not defined to replace the regular Jinja rendering done for creating the Intended configuration, only to add secrets information on the fly. This avoids undesired behavior on this synchronous operation.

This function performs an additional permission validation, to check if the requesting user has permissions to view the `SecretsGroup` requested.

### Configuration Compliance 

Over time device(s) platform may change; whether this is a device refresh or full replacement. A Django `post_save` signal is used on the `ConfigCompliance` model and provides a reliable and efficient way to manage configuration compliance objects. This signal deletes any `ConfigCompliance` objects that don't match the current platform. This decision was made to avoid compliance reporting inconsistencies that can arise when outdated or irrelevant objects remain in the database which were generated with the previous platform.

This has a computational impact when updating a Device object's platform. This is similar to the computational impact of an SQL `cascade` option on a delete. This is largely unavoidable and should be limited in impact, such that it will only be the removal of the number of `ConfigCompliance` objects, which is no bigger than the number of  `Config Features`, which is generally intended to be a small amount.

### Configuration Deployment and Remediation

Configuration remediation and deployments of any of the attributes based on the configuration compliance object are calculated based on the last run of the `ConfigCompliance` job. After a configuration deployment to fix any of these attributes (remediation, intended, missing) a new `ConfigCompliance` job must be run before all the compliance results will be updated.


### Manual ConfigPlans

When generating a manual `ConfigPlan` the Jinja2 template render has access to Django ORM methods like `.all()`, this also means that methods like `.delete()` can be called, the `render_template` functionality used by Golden Config inherits a Jinja2 Sandbox exception that will block unsafe calls. Golden Config will simply re-raise the exception `jinja2.exceptions.SecurityError: > is not safely callable`.


### Hidden Jobs and JobButtons

The configuration deployment and plans features of Golden Config come packaged with Jobs and JobButtons to execute the functionality. In order to to provide a repeatable and consistent behavior these Jobs and JobButtons are designed to only be executed via specialized views. They're not intended to be executed manually from the Jobs/JobButtons menus.
