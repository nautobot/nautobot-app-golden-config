"""Django Models for tracking the configuration compliance per feature and device."""

import json
import logging
import os

from deepdiff import DeepDiff
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.manager import BaseManager
from django.utils.module_loading import import_string
from hier_config import Host as HierConfigHost
from nautobot.apps.models import RestrictedQuerySet
from nautobot.apps.utils import render_jinja2
from nautobot.core.models.generics import PrimaryModel
from nautobot.core.models.utils import serialize_object, serialize_object_v2
from nautobot.dcim.models import Device
from nautobot.extras.models import ObjectChange
from nautobot.extras.models.statuses import StatusField
from nautobot.extras.utils import extras_features
from netutils.config.compliance import feature_compliance
from xmldiff import actions, main

from nautobot_golden_config.choices import ComplianceRuleConfigTypeChoice, ConfigPlanTypeChoice, RemediationTypeChoice
from nautobot_golden_config.utilities.constant import ENABLE_SOTAGG, PLUGIN_CFG

LOGGER = logging.getLogger(__name__)
GRAPHQL_STR_START = "query ($device_id: ID!)"

ERROR_MSG = (
    "There was an issue with the data that was returned by your get_custom_compliance function. "
    "This is a local issue that requires the attention of your systems administrator and not something "
    "that can be fixed within the Golden Config app. "
)
MISSING_MSG = (
    ERROR_MSG + "Specifically the `{}` key was not found in value the get_custom_compliance function provided."
)
VALIDATION_MSG = (
    ERROR_MSG + "Specifically the key {} was expected to be of type(s) {} and the value of {} was not that type(s)."
)

CUSTOM_FUNCTIONS = {
    "get_custom_compliance": "custom",
    "get_custom_remediation": RemediationTypeChoice.TYPE_CUSTOM,
}


def _is_jsonable(val):
    """Check is value can be converted to json."""
    try:
        json.dumps(val)
        return True
    except (TypeError, OverflowError):
        return False


def _null_to_empty(val):
    """Convert to empty string if the value is currently null."""
    if not val:
        return ""
    return val


def _get_cli_compliance(obj):
    """This function performs the actual compliance for cli configuration."""
    feature = {
        "ordered": obj.rule.config_ordered,
        "name": obj.rule,
    }
    feature.update({"section": obj.rule.match_config.splitlines()})
    value = feature_compliance(
        feature, obj.actual, obj.intended, obj.device.platform.network_driver_mappings.get("netutils_parser")
    )
    compliance = value["compliant"]
    if compliance:
        compliance_int = 1
        ordered = value["ordered_compliant"]
    else:
        compliance_int = 0
        ordered = value["ordered_compliant"]
    missing = _null_to_empty(value["missing"])
    extra = _null_to_empty(value["extra"])
    return {
        "compliance": compliance,
        "compliance_int": compliance_int,
        "ordered": ordered,
        "missing": missing,
        "extra": extra,
    }


def _get_json_compliance(obj):
    """This function performs the actual compliance for json serializable data."""

    def _normalize_diff(diff, path_to_diff):
        """Normalizes the diff to a list of keys and list indexes that have changed."""
        dictionary_items = list(diff.get(f"dictionary_item_{path_to_diff}", []))
        list_items = list(diff.get(f"iterable_item_{path_to_diff}", {}).keys())
        values_changed = list(diff.get("values_changed", {}).keys())
        type_changes = list(diff.get("type_changes", {}).keys())
        return dictionary_items + list_items + values_changed + type_changes

    diff = DeepDiff(obj.actual, obj.intended, ignore_order=obj.ordered, report_repetition=True)
    if not diff:
        compliance_int = 1
        compliance = True
        ordered = True
        missing = ""
        extra = ""
    else:
        compliance_int = 0
        compliance = False
        ordered = False
        missing = _null_to_empty(_normalize_diff(diff, "added"))
        extra = _null_to_empty(_normalize_diff(diff, "removed"))

    return {
        "compliance": compliance,
        "compliance_int": compliance_int,
        "ordered": ordered,
        "missing": missing,
        "extra": extra,
    }


def _get_xml_compliance(obj):
    """This function performs the actual compliance for xml serializable data."""

    def _normalize_diff(diff):
        """Format the diff output to a list of nodes with values that have updated."""
        formatted_diff = []
        for operation in diff:
            if isinstance(operation, actions.UpdateTextIn):
                formatted_operation = f"{operation.node}, {operation.text}"
                formatted_diff.append(formatted_operation)
        return "\n".join(formatted_diff)

    # Options for the diff operation. These are set to prefer updates over node insertions/deletions.
    diff_options = {
        "F": 0.1,
        "fast_match": True,
    }
    missing = main.diff_texts(obj.actual, obj.intended, diff_options=diff_options)
    extra = main.diff_texts(obj.intended, obj.actual, diff_options=diff_options)

    compliance = not missing and not extra
    compliance_int = int(compliance)
    ordered = obj.ordered
    missing = _null_to_empty(_normalize_diff(missing))
    extra = _null_to_empty(_normalize_diff(extra))

    return {
        "compliance": compliance,
        "compliance_int": compliance_int,
        "ordered": ordered,
        "missing": missing,
        "extra": extra,
    }


def _verify_get_custom_compliance_data(compliance_details):
    """This function verifies the data is as expected when a custom function is used."""
    for val in ["compliance", "compliance_int", "ordered", "missing", "extra"]:
        try:
            compliance_details[val]
        except KeyError:
            raise ValidationError(MISSING_MSG.format(val)) from KeyError
    for val in ["compliance", "ordered"]:
        if compliance_details[val] not in [True, False]:
            raise ValidationError(VALIDATION_MSG.format(val, "Boolean", compliance_details[val]))
    if compliance_details["compliance_int"] not in [0, 1]:
        raise ValidationError(VALIDATION_MSG.format("compliance_int", "0 or 1", compliance_details["compliance_int"]))
    for val in ["missing", "extra"]:
        if not isinstance(compliance_details[val], str) and not _is_jsonable(compliance_details[val]):
            raise ValidationError(VALIDATION_MSG.format(val, "String or Json", compliance_details[val]))


def _get_hierconfig_remediation(obj):
    """Returns the remediating config."""
    hierconfig_os = obj.device.platform.network_driver_mappings["hier_config"]
    if not hierconfig_os:
        raise ValidationError(f"platform {obj.network_driver} is not supported by hierconfig.")

    try:
        remediation_setting_obj = RemediationSetting.objects.get(platform=obj.rule.platform)
    except Exception as err:  # pylint: disable=broad-except:
        raise ValidationError(f"Platform {obj.network_driver} has no Remediation Settings defined.") from err

    remediation_options = remediation_setting_obj.remediation_options

    try:
        hc_kwargs = {"hostname": obj.device.name, "os": hierconfig_os}
        if remediation_options:
            hc_kwargs.update(hconfig_options=remediation_options)
        host = HierConfigHost(**hc_kwargs)

    except Exception as err:  # pylint: disable=broad-except:
        raise Exception(  # pylint: disable=broad-exception-raised
            f"Cannot instantiate HierConfig on {obj.device.name}, check Device, Platform and Hier Options."
        ) from err

    host.load_generated_config(obj.intended)
    host.load_running_config(obj.actual)
    host.remediation_config()
    remediation_config = host.remediation_config_filtered_text(include_tags={}, exclude_tags={})

    return remediation_config


# The below maps the provided compliance types
FUNC_MAPPER = {
    ComplianceRuleConfigTypeChoice.TYPE_CLI: _get_cli_compliance,
    ComplianceRuleConfigTypeChoice.TYPE_JSON: _get_json_compliance,
    ComplianceRuleConfigTypeChoice.TYPE_XML: _get_xml_compliance,
    RemediationTypeChoice.TYPE_HIERCONFIG: _get_hierconfig_remediation,
}
# The below conditionally add the custom provided compliance type
for custom_function, custom_type in CUSTOM_FUNCTIONS.items():
    if PLUGIN_CFG.get(custom_function):
        try:
            FUNC_MAPPER[custom_type] = import_string(PLUGIN_CFG[custom_function])
        except Exception as error:  # pylint: disable=broad-except
            msg = (
                "There was an issue attempting to import the custom function of"
                f"{PLUGIN_CFG[custom_function]}, this is expected with a local configuration issue "
                "and not related to the Golden Configuration App, please contact your system admin for further details"
            )
            raise Exception(msg).with_traceback(error.__traceback__)


@extras_features(
    "custom_fields",
    "custom_validators",
    "export_templates",
    "graphql",
    "relationships",
    "webhooks",
)
class ComplianceFeature(PrimaryModel):  # pylint: disable=too-many-ancestors
    """ComplianceFeature details."""

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.CharField(max_length=200, blank=True)

    class Meta:
        """Meta information for ComplianceFeature model."""

        ordering = ("slug",)

    def __str__(self):
        """Return a sane string representation of the instance."""
        return self.slug


@extras_features(
    "custom_fields",
    "custom_validators",
    "export_templates",
    "graphql",
    "relationships",
    "webhooks",
)
class ComplianceRule(PrimaryModel):  # pylint: disable=too-many-ancestors
    """ComplianceRule details."""

    feature = models.ForeignKey(to="ComplianceFeature", on_delete=models.CASCADE, related_name="feature")

    platform = models.ForeignKey(
        to="dcim.Platform",
        on_delete=models.CASCADE,
        related_name="compliance_rules",
    )
    description = models.CharField(
        max_length=200,
        blank=True,
    )
    config_ordered = models.BooleanField(
        verbose_name="Configured Ordered",
        help_text="Whether or not the configuration order matters, such as in ACLs.",
        default=False,
    )

    config_remediation = models.BooleanField(
        default=False,
        verbose_name="Config Remediation",
        help_text="Whether or not the config remediation is executed for this compliance rule.",
    )

    match_config = models.TextField(
        blank=True,
        verbose_name="Config to Match",
        help_text="The config to match that is matched based on the parent most configuration. E.g.: For CLI `router bgp` or `ntp`. For JSON this is a top level key name. For XML this is a xpath query.",
    )
    config_type = models.CharField(
        max_length=20,
        default=ComplianceRuleConfigTypeChoice.TYPE_CLI,
        choices=ComplianceRuleConfigTypeChoice,
        help_text="Whether the configuration is in CLI, JSON, or XML format.",
    )
    custom_compliance = models.BooleanField(
        default=False, help_text="Whether this Compliance Rule is proceeded as custom."
    )

    @property
    def remediation_setting(self):
        """Returns remediation settings for a particular platform."""
        return RemediationSetting.objects.filter(platform=self.platform).first()

    class Meta:
        """Meta information for ComplianceRule model."""

        ordering = ("platform", "feature__name")
        unique_together = (
            "feature",
            "platform",
        )

    def __str__(self):
        """Return a sane string representation of the instance."""
        return f"{self.platform} - {self.feature.name}"

    def clean(self):
        """Verify that if cli, then match_config is set."""
        if self.config_type == ComplianceRuleConfigTypeChoice.TYPE_CLI and not self.match_config:
            raise ValidationError("CLI configuration set, but no configuration set to match.")


@extras_features(
    "custom_fields",
    "custom_links",
    "custom_validators",
    "export_templates",
    "graphql",
    "relationships",
    "webhooks",
)
class ConfigCompliance(PrimaryModel):  # pylint: disable=too-many-ancestors
    """Configuration compliance details."""

    device = models.ForeignKey(to="dcim.Device", on_delete=models.CASCADE, help_text="The device")
    rule = models.ForeignKey(to="ComplianceRule", on_delete=models.CASCADE, related_name="rule")
    compliance = models.BooleanField(blank=True)
    actual = models.JSONField(blank=True, help_text="Actual Configuration for feature")
    intended = models.JSONField(blank=True, help_text="Intended Configuration for feature")
    # these three are config snippets exposed for the ConfigDeployment.
    remediation = models.JSONField(blank=True, help_text="Remediation Configuration for the device")
    missing = models.JSONField(blank=True, help_text="Configuration that should be on the device.")
    extra = models.JSONField(blank=True, help_text="Configuration that should not be on the device.")
    ordered = models.BooleanField(default=False)
    # Used for django-pivot, both compliance and compliance_int should be set.
    compliance_int = models.IntegerField(blank=True)

    def to_objectchange(self, action, *, related_object=None, object_data_extra=None, object_data_exclude=None):  # pylint: disable=arguments-differ
        """Remove actual and intended configuration from changelog."""
        fields_to_exclude = ["actual", "intended"]
        if not object_data_exclude:
            object_data_exclude = fields_to_exclude
        data_v2 = serialize_object_v2(self)
        for field in fields_to_exclude:
            data_v2.pop(field)
        return ObjectChange(
            changed_object=self,
            object_repr=str(self),
            action=action,
            object_data=serialize_object(self, extra=object_data_extra, exclude=object_data_exclude),
            object_data_v2=data_v2,
            related_object=related_object,
        )

    is_dynamic_group_associable_model = False

    class Meta:
        """Set unique together fields for model."""

        ordering = ["device", "rule"]
        unique_together = ("device", "rule")

    def __str__(self):
        """String representation of a the compliance."""
        return f"{self.device} -> {self.rule} -> {self.compliance}"

    def compliance_on_save(self):
        """The actual configuration compliance happens here, but the details for actual compliance job would be found in FUNC_MAPPER."""
        if self.rule.custom_compliance:
            if not FUNC_MAPPER.get("custom"):
                raise ValidationError(
                    "Custom type provided, but no `get_custom_compliance` config set, please contact system admin."
                )
            compliance_details = FUNC_MAPPER["custom"](obj=self)
            _verify_get_custom_compliance_data(compliance_details)
        else:
            compliance_details = FUNC_MAPPER[self.rule.config_type](obj=self)

        self.compliance = compliance_details["compliance"]
        self.compliance_int = compliance_details["compliance_int"]
        self.ordered = compliance_details["ordered"]
        self.missing = compliance_details["missing"]
        self.extra = compliance_details["extra"]

    def remediation_on_save(self):
        """The actual remediation happens here, before saving the object."""
        if self.compliance:
            self.remediation = ""
            return

        if not self.rule.config_remediation:
            self.remediation = ""
            return

        if not self.rule.remediation_setting:
            self.remediation = ""
            return

        remediation_config = FUNC_MAPPER[self.rule.remediation_setting.remediation_type](obj=self)
        self.remediation = remediation_config

    def save(self, *args, **kwargs):
        """The actual configuration compliance happens here, but the details for actual compliance job would be found in FUNC_MAPPER."""
        self.compliance_on_save()
        self.remediation_on_save()
        self.full_clean()

        # This accounts for django 4.2 `Setting update_fields in Model.save() may now be required` change
        # in behavior
        if kwargs.get("update_fields"):
            kwargs["update_fields"].update(
                {"compliance", "compliance_int", "ordered", "missing", "extra", "remediation"}
            )

        super().save(*args, **kwargs)


@extras_features(
    "custom_fields",
    "custom_links",
    "custom_validators",
    "export_templates",
    "graphql",
    "relationships",
    "webhooks",
)
class GoldenConfig(PrimaryModel):  # pylint: disable=too-many-ancestors
    """Configuration Management Model."""

    device = models.OneToOneField(
        to="dcim.Device",
        on_delete=models.CASCADE,
        help_text="device",
        blank=False,
    )
    backup_config = models.TextField(blank=True, help_text="Full backup config for device.")
    backup_last_attempt_date = models.DateTimeField(null=True, blank=True)
    backup_last_success_date = models.DateTimeField(null=True, blank=True)

    intended_config = models.TextField(blank=True, help_text="Intended config for the device.")
    intended_last_attempt_date = models.DateTimeField(null=True, blank=True)
    intended_last_success_date = models.DateTimeField(null=True, blank=True)

    compliance_config = models.TextField(blank=True, help_text="Full config diff for device.")
    compliance_last_attempt_date = models.DateTimeField(null=True, blank=True)
    compliance_last_success_date = models.DateTimeField(null=True, blank=True)

    def to_objectchange(self, action, *, related_object=None, object_data_extra=None, object_data_exclude=None):  # pylint: disable=arguments-differ
        """Remove actual and intended configuration from changelog."""
        fields_to_exclude = ["backup_config", "intended_config", "compliance_config"]
        if not object_data_exclude:
            object_data_exclude = fields_to_exclude
        data_v2 = serialize_object_v2(self)
        for field in fields_to_exclude:
            data_v2.pop(field)
        return ObjectChange(
            changed_object=self,
            object_repr=str(self),
            action=action,
            object_data=serialize_object(self, extra=object_data_extra, exclude=object_data_exclude),
            object_data_v2=data_v2,
            related_object=related_object,
        )

    @staticmethod
    def get_dynamic_group_device_pks():
        """Get all Device PKs associated with GoldenConfigSetting DynamicGroups."""
        gc_dynamic_group_device_queryset = Device.objects.none()
        for setting in GoldenConfigSetting.objects.all():
            # using "|" should not require calling distinct afterwards
            gc_dynamic_group_device_queryset = gc_dynamic_group_device_queryset | setting.dynamic_group.members

        return set(gc_dynamic_group_device_queryset.values_list("pk", flat=True))

    @classmethod
    def get_golden_config_device_ids(cls):
        """Get all Device PKs associated with GoldenConfig entries."""
        return set(cls.objects.values_list("device__pk", flat=True))

    class Meta:
        """Set unique together fields for model."""

        ordering = ["device"]

    def __str__(self):
        """String representation of a the compliance."""
        return f"{self.device}"


class GoldenConfigSettingManager(BaseManager.from_queryset(RestrictedQuerySet)):
    """Manager for GoldenConfigSetting."""

    def get_for_device(self, device):
        """Return the highest weighted GoldenConfigSetting assigned to a device."""
        if not isinstance(device, Device):
            raise ValueError("The device argument must be a Device instance.")
        dynamic_group = device.dynamic_groups.exclude(golden_config_setting__isnull=True)
        if dynamic_group.exists():
            return dynamic_group.order_by("-golden_config_setting__weight").first().golden_config_setting
        return None


@extras_features(
    "graphql",
)
class GoldenConfigSetting(PrimaryModel):  # pylint: disable=too-many-ancestors
    """GoldenConfigSetting Model definition. This provides global configs instead of via configs.py."""

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    weight = models.PositiveSmallIntegerField(default=1000)
    description = models.CharField(
        max_length=200,
        blank=True,
    )
    backup_repository = models.ForeignKey(
        to="extras.GitRepository",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="backup_repository",
        limit_choices_to={"provided_contents__contains": "nautobot_golden_config.backupconfigs"},
    )
    backup_path_template = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Backup Path in Jinja Template Form",
        help_text="The Jinja path representation of where the backup file will be found. The variable `obj` is available as the device instance object of a given device, as is the case for all Jinja templates. e.g. `{{obj.location.name|slugify}}/{{obj.name}}.cfg`",
    )
    intended_repository = models.ForeignKey(
        to="extras.GitRepository",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="intended_repository",
        limit_choices_to={"provided_contents__contains": "nautobot_golden_config.intendedconfigs"},
    )
    intended_path_template = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Intended Path in Jinja Template Form",
        help_text="The Jinja path representation of where the generated file will be placed. e.g. `{{obj.location.name|slugify}}/{{obj.name}}.cfg`",
    )
    jinja_repository = models.ForeignKey(
        to="extras.GitRepository",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="jinja_template",
        limit_choices_to={"provided_contents__contains": "nautobot_golden_config.jinjatemplate"},
    )
    jinja_path_template = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Template Path in Jinja Template Form",
        help_text="The Jinja path representation of where the Jinja template can be found. e.g. `{{obj.platform.network_driver}}.j2`",
    )
    backup_test_connectivity = models.BooleanField(
        default=True,
        verbose_name="Backup Test",
        help_text="Whether or not to pretest the connectivity of the device by verifying there is a resolvable IP that can connect to port 22.",
    )
    sot_agg_query = models.ForeignKey(
        to="extras.GraphQLQuery",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="sot_aggregation",
    )
    dynamic_group = models.OneToOneField(
        to="extras.DynamicGroup",
        on_delete=models.PROTECT,
        related_name="golden_config_setting",
    )
    is_dynamic_group_associable_model = False

    objects = GoldenConfigSettingManager()

    def __str__(self):
        """Return a simple string if model is called."""
        return f"Golden Config Setting - {self.name}"

    class Meta:
        """Set unique fields for model.

        Provide ordering used in tables and get_device_to_settings_map.
        Sorting on weight is performed from the highest weight value to the lowest weight value.
        This is to ensure only one app settings could be applied per single device based on priority and name.
        """

        verbose_name = "Golden Config Setting"
        ordering = ["-weight", "name"]  # Refer to weight comment in class docstring.

    def clean(self):
        """Validate the scope and GraphQL query."""
        super().clean()

        if ENABLE_SOTAGG and not self.sot_agg_query:
            raise ValidationError("A GraphQL query must be defined when `ENABLE_SOTAGG` is True")

        if self.sot_agg_query:
            LOGGER.debug("GraphQL - test  query start with: `%s`", GRAPHQL_STR_START)
            if not str(self.sot_agg_query.query.lstrip()).startswith(GRAPHQL_STR_START):
                raise ValidationError(f"The GraphQL query must start with exactly `{GRAPHQL_STR_START}`")

    def get_queryset(self):
        """Generate a Device QuerySet from the filter."""
        return self.dynamic_group.members

    def device_count(self):
        """Return the number of devices in the group."""
        return self.dynamic_group.count

    def get_url_to_filtered_device_list(self):
        """Get url to all devices that are matching the filter."""
        return self.dynamic_group.get_group_members_url()

    def get_jinja_template_path_for_device(self, device):
        """Get the Jinja template path for a device."""
        if self.jinja_repository is not None:
            rendered_path = render_jinja2(template_code=self.jinja_path_template, context={"obj": device})
            return f"{self.jinja_repository.filesystem_path}{os.path.sep}{rendered_path}"
        return None


@extras_features(
    "custom_fields",
    "custom_links",
    "custom_validators",
    "export_templates",
    "graphql",
    "relationships",
    "webhooks",
)
class ConfigRemove(PrimaryModel):  # pylint: disable=too-many-ancestors
    """ConfigRemove for Regex Line Removals from Backup Configuration Model definition."""

    name = models.CharField(max_length=255)
    platform = models.ForeignKey(
        to="dcim.Platform",
        on_delete=models.CASCADE,
        related_name="backup_line_remove",
    )
    description = models.CharField(
        max_length=200,
        blank=True,
    )
    regex = models.CharField(
        max_length=200,
        verbose_name="Regex Pattern",
        help_text="Regex pattern used to remove a line from the backup configuration.",
    )

    clone_fields = ["platform", "description", "regex"]

    class Meta:
        """Meta information for ConfigRemove model."""

        ordering = ("platform", "name")
        unique_together = ("name", "platform")

    def __str__(self):
        """Return a simple string if model is called."""
        return self.name


@extras_features(
    "custom_fields",
    "custom_links",
    "custom_validators",
    "export_templates",
    "graphql",
    "relationships",
    "webhooks",
)
class ConfigReplace(PrimaryModel):  # pylint: disable=too-many-ancestors
    """ConfigReplace for Regex Line Replacements from Backup Configuration Model definition."""

    name = models.CharField(max_length=255)
    platform = models.ForeignKey(
        to="dcim.Platform",
        on_delete=models.CASCADE,
        related_name="backup_line_replace",
    )
    description = models.CharField(
        max_length=200,
        blank=True,
    )
    regex = models.CharField(
        max_length=200,
        verbose_name="Regex Pattern to Substitute",
        help_text="Regex pattern that will be found and replaced with 'replaced text'.",
    )
    replace = models.CharField(
        max_length=200,
        verbose_name="Replaced Text",
        help_text="Text that will be inserted in place of Regex pattern match.",
    )

    clone_fields = ["platform", "description", "regex", "replace"]

    class Meta:
        """Meta information for ConfigReplace model."""

        ordering = ("platform", "name")
        unique_together = ("name", "platform")

    def __str__(self):
        """Return a simple string if model is called."""
        return self.name


@extras_features(
    "custom_fields",
    "custom_links",
    "custom_validators",
    "export_templates",
    "graphql",
    "relationships",
    "webhooks",
)
class RemediationSetting(PrimaryModel):  # pylint: disable=too-many-ancestors
    """RemediationSetting details."""

    # Remediation points to the platform
    platform = models.OneToOneField(
        to="dcim.Platform",
        on_delete=models.CASCADE,
        related_name="remediation_settings",
    )

    remediation_type = models.CharField(
        max_length=50,
        default=RemediationTypeChoice.TYPE_HIERCONFIG,
        choices=RemediationTypeChoice,
        help_text="Whether the remediation setting is type HierConfig or custom.",
    )

    # takes options.json.
    remediation_options = models.JSONField(
        blank=True,
        default=dict,
        help_text="Remediation Configuration for the device",
    )

    csv_headers = [
        "platform",
        "remediation_type",
    ]

    class Meta:
        """Meta information for RemediationSettings model."""

        ordering = ("platform", "remediation_type")

    def to_csv(self):
        """Indicates model fields to return as csv."""
        return (
            self.platform,
            self.remediation_type,
        )

    def __str__(self):
        """Return a sane string representation of the instance."""
        return str(self.platform)


@extras_features(
    "custom_fields",
    "custom_links",
    "custom_validators",
    "export_templates",
    "graphql",
    "relationships",
    "webhooks",
    "statuses",
)
class ConfigPlan(PrimaryModel):  # pylint: disable=too-many-ancestors
    """ConfigPlan for Golden Configuration Plan Model definition."""

    plan_type = models.CharField(max_length=20, choices=ConfigPlanTypeChoice, verbose_name="Plan Type")
    device = models.ForeignKey(
        to="dcim.Device",
        on_delete=models.CASCADE,
        related_name="config_plan",
    )
    config_set = models.TextField(help_text="Configuration set to be applied to device.")
    feature = models.ManyToManyField(
        to=ComplianceFeature,
        related_name="config_plan",
        blank=True,
    )
    plan_result = models.ForeignKey(
        to="extras.JobResult",
        on_delete=models.CASCADE,
        related_name="config_plan",
        verbose_name="Plan Result",
    )
    deploy_result = models.ForeignKey(
        to="extras.JobResult",
        on_delete=models.PROTECT,
        related_name="config_plan_deploy_result",
        verbose_name="Deploy Result",
        blank=True,
        null=True,
    )
    change_control_id = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Change Control ID",
        help_text="Change Control ID for this configuration plan.",
    )
    change_control_url = models.URLField(blank=True, verbose_name="Change Control URL")
    status = StatusField(blank=True, null=True, on_delete=models.PROTECT)

    class Meta:
        """Meta information for ConfigPlan model."""

        ordering = ("-created", "device")
        unique_together = (
            "plan_type",
            "device",
            "created",
        )

    def __str__(self):
        """Return a simple string if model is called."""
        return f"{self.device.name}-{self.plan_type}-{self.created}"
