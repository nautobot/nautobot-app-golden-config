"""Data source plugin extension to register additional git repo types."""
import os
from django.db import IntegrityError
import yaml
from nautobot.extras.choices import LogLevelChoices
from nautobot.extras.registry import DatasourceContent
from nautobot.dcim.models.devices import Platform

from nautobot_golden_config.utilities.constant import ENABLE_BACKUP, ENABLE_COMPLIANCE, ENABLE_INTENDED
from nautobot_golden_config.models import ComplianceFeature, ComplianceRule, ConfigReplace, ConfigRemove
from nautobot_golden_config.exceptions import MissingReference


def refresh_git_jinja(repository_record, job_result, delete=False):  # pylint: disable=unused-argument
    """Callback for gitrepository updates on Jinja Template repo."""
    job_result.log(
        "Successfully Pulled git repo",
        level_choice=LogLevelChoices.LOG_SUCCESS,
    )


def refresh_git_intended(repository_record, job_result, delete=False):  # pylint: disable=unused-argument
    """Callback for gitrepository updates on Intended Config repo."""
    job_result.log(
        "Successfully Pulled git repo",
        level_choice=LogLevelChoices.LOG_SUCCESS,
    )


def refresh_git_backup(repository_record, job_result, delete=False):  # pylint: disable=unused-argument
    """Callback for gitrepository updates on Git Backup repo."""
    job_result.log(
        "Successfully Pulled git repo",
        level_choice=LogLevelChoices.LOG_SUCCESS,
    )


def refresh_git_gc_properties(repository_record, job_result, delete=False):  # pylint: disable=unused-argument
    """Callback for gitrepository updates on Git Configuration repo.

    Expected folder structure:
    ├── golden_config
    │   ├── compliance_features
    │   ├── compliance_rules
    │   ├── config_removes
    │   ├── config_replaces

    """
    golden_config_path = os.path.join(repository_record.filesystem_path, "golden_config")
    if not os.path.isdir(golden_config_path):
        job_result.log(
            f"Skipping sync for {golden_config_path} because directory doesn't exist.",
            level_choice=LogLevelChoices.LOG_INFO,
        )
        return

    # gc_config_items parametrize the method to import the different GC properties
    # "directory_name": is the directory name under golden_config
    # "class": is the Django model related to the property
    # "id_keys": is a tuple of tuples, defining the attributes that identify an instance. The inner tuple
    #   defines the mapping from the YAML to the actual attribute name.
    gc_config_items = (
        {
            "directory_name": "compliance_features",
            "class": ComplianceFeature,
            "id_keys": (("name", "name"),),
        },
        {
            "directory_name": "compliance_rules",
            "class": ComplianceRule,
            "id_keys": (
                ("feature", "feature_slug"),
                ("platform", "platform_slug"),
            ),
        },
        {
            "directory_name": "config_removes",
            "class": ConfigRemove,
            "id_keys": (
                ("name", "name"),
                ("platform", "platform_slug"),
            ),
        },
        {
            "directory_name": "config_replaces",
            "class": ConfigReplace,
            "id_keys": (
                ("name", "name"),
                ("platform", "platform_slug"),
            ),
        },
    )

    for gc_config_item in gc_config_items:
        update_git_gc_properties(golden_config_path, job_result, gc_config_item)

    job_result.log(
        "Successfully Completed sync of Golden Config properties",
        level_choice=LogLevelChoices.LOG_SUCCESS,
    )


def get_id_kwargs(gc_config_item_dict, id_keys, job_result):
    """Method to get the proper id kwargs and remove them from gc_config_item_dict."""
    # fk_slug_class_mapping contains a mapping of the FK attributes to the related model
    fk_slug_class_mapping = {"feature": ComplianceFeature, "platform": Platform}

    id_kwargs = {}
    for id_key in id_keys:
        actual_attr_name = id_key[0]
        yaml_attr_name = id_key[1]

        # If the attribute is actually a FK reference, we need to resolve the related object
        if actual_attr_name in fk_slug_class_mapping:
            try:
                id_kwargs[actual_attr_name] = fk_slug_class_mapping[actual_attr_name].objects.get(
                    slug=gc_config_item_dict[yaml_attr_name]
                )
            except fk_slug_class_mapping[actual_attr_name].DoesNotExist:
                job_result.log(
                    (
                        f"Reference to {yaml_attr_name}: {gc_config_item_dict[yaml_attr_name]}",
                        "is not available.",
                    ),
                    level_choice=LogLevelChoices.LOG_WARNING,
                )
                raise MissingReference from fk_slug_class_mapping[actual_attr_name].DoesNotExist
        else:
            id_kwargs[actual_attr_name] = gc_config_item_dict[yaml_attr_name]

        # We remove the attributes used to identify the item from the defaults dictionary
        del gc_config_item_dict[yaml_attr_name]

    return id_kwargs


def update_git_gc_properties(golden_config_path, job_result, gc_config_item):  # pylint: disable=too-many-locals
    """Refresh any compliance features provided by this Git repository."""
    gc_config_item_path = os.path.join(golden_config_path, gc_config_item["directory_name"])
    if not os.path.isdir(gc_config_item_path):
        job_result.log(
            f"Skipping sync for {gc_config_item['directory_name']} because directory doesn't exist.",
            level_choice=LogLevelChoices.LOG_INFO,
        )
        return

    property_model = gc_config_item["class"]

    job_result.log(
        f"Refreshing {property_model.__name__}...",
        level_choice=LogLevelChoices.LOG_INFO,
    )

    file_names = []
    for root, _, files in os.walk(gc_config_item_path):
        for file_name in files:
            if not any(file_name.endswith(yaml_extension) for yaml_extension in (".yml", ".yaml")):
                continue
            file_names.append({"root": root, "file_name": file_name})

    for details in file_names:
        root = details["root"]
        file_name = details["file_name"]

        with open(os.path.join(root, file_name), "r", encoding="utf-8") as yaml_file:
            try:
                gc_config_property_list = yaml.safe_load(yaml_file)

            except yaml.YAMLError as exc:
                job_result.log(
                    f"Error loading {os.path.join(root, file_name)}: {exc}",
                    level_choice=LogLevelChoices.LOG_WARNING,
                )
                continue

        try:
            for item_dict in gc_config_property_list:
                id_kwargs = get_id_kwargs(item_dict, gc_config_item["id_keys"], job_result)
                item, created = gc_config_item["class"].objects.update_or_create(**id_kwargs, defaults=item_dict)

                log_message = (
                    f"New {property_model.__name__} created: {item}"
                    if created
                    else f"Updated {property_model.__name__}: {item}"
                )

                job_result.log(
                    log_message,
                    level_choice=LogLevelChoices.LOG_SUCCESS,
                )

        except MissingReference:
            continue

        except IntegrityError as exc:
            job_result.log(
                f"Issue seen with attribute values: {exc}",
                level_choice=LogLevelChoices.LOG_WARNING,
            )
            continue


datasource_contents = []
if ENABLE_INTENDED or ENABLE_COMPLIANCE:
    datasource_contents.append(
        (
            "extras.gitrepository",
            DatasourceContent(
                name="intended configs",
                content_identifier="nautobot_golden_config.intendedconfigs",
                icon="mdi-file-document-outline",
                callback=refresh_git_intended,
            ),
        )
    )
if ENABLE_INTENDED:
    datasource_contents.append(
        (
            "extras.gitrepository",
            DatasourceContent(
                name="jinja templates",
                content_identifier="nautobot_golden_config.jinjatemplate",
                icon="mdi-text-box-check-outline",
                callback=refresh_git_jinja,
            ),
        )
    )
if ENABLE_BACKUP or ENABLE_COMPLIANCE:
    datasource_contents.append(
        (
            "extras.gitrepository",
            DatasourceContent(
                name="backup configs",
                content_identifier="nautobot_golden_config.backupconfigs",
                icon="mdi-file-code",
                callback=refresh_git_backup,
            ),
        )
    )

datasource_contents.append(
    (
        "extras.gitrepository",
        DatasourceContent(
            name="Golden Config properties",
            content_identifier="nautobot_golden_config.pluginproperties",
            icon="mdi-file-code",
            callback=refresh_git_gc_properties,
        ),
    )
)
