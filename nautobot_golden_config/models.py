"""Django Models for tracking the configuration compliance per feature and device."""

import logging
import json
from deepdiff import DeepDiff
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.shortcuts import reverse
from django.utils.module_loading import import_string
from django.utils.text import slugify

from nautobot.extras.models import ObjectChange, DynamicGroup
from nautobot.extras.utils import extras_features
from nautobot.utilities.utils import serialize_object, serialize_object_v2
from nautobot.core.models.generics import PrimaryModel
from netutils.config.compliance import feature_compliance

from nautobot_golden_config.choices import ComplianceRuleTypeChoice
from nautobot_golden_config.utilities.utils import get_platform
from nautobot_golden_config.utilities.constant import PLUGIN_CFG


LOGGER = logging.getLogger(__name__)
GRAPHQL_STR_START = "query ($device_id: ID!)"

ERROR_MSG = (
    "There was an issue with the data that was returned by your get_custom_compliance function. "
    "This is a local issue that requires the attention of your systems administrator and not something "
    "that can be fixed within the Golden Config plugin. "
)
MISSING_MSG = (
    ERROR_MSG + "Specifically the `{}` key was not found in value the get_custom_compliance function provided."
)
VALIDATION_MSG = (
    ERROR_MSG + "Specifically the key {} was expected to be of type(s) {} and the value of {} was not that type(s)."
)


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
    value = feature_compliance(feature, obj.actual, obj.intended, get_platform(obj.device.platform.slug))
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


# The below maps the provided compliance types
FUNC_MAPPER = {
    ComplianceRuleTypeChoice.TYPE_CLI: _get_cli_compliance,
    ComplianceRuleTypeChoice.TYPE_JSON: _get_json_compliance,
}
# The below conditionally add the cusom provided compliance type
if PLUGIN_CFG.get("get_custom_compliance"):
    try:
        FUNC_MAPPER[ComplianceRuleTypeChoice.TYPE_CUSTOM] = import_string(PLUGIN_CFG["get_custom_compliance"])
    except Exception as error:  # pylint: disable=broad-except
        msg = (
            "There was an issue attempting to import the get_custom_compliance function of"
            f"{PLUGIN_CFG['get_custom_compliance']}, this is expected with a local configuration issue "
            "and not related to the Golden Configuration Plugin, please contact your system admin for further details"
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

    csv_headers = ["name", "slug", "description"]

    def to_csv(self):
        """Indicates model fields to return as csv."""
        return (self.name, self.slug, self.description)

    class Meta:
        """Meta information for ComplianceFeature model."""

        ordering = ("slug",)

    def __str__(self):
        """Return a sane string representation of the instance."""
        return self.slug

    def get_absolute_url(self):
        """Absolute url for the ComplianceFeature instance."""
        return reverse("plugins:nautobot_golden_config:compliancefeature", args=[self.pk])


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

    feature = models.ForeignKey(to="ComplianceFeature", on_delete=models.CASCADE, blank=False, related_name="feature")

    platform = models.ForeignKey(
        to="dcim.Platform",
        on_delete=models.CASCADE,
        related_name="compliance_rules",
        null=False,
        blank=False,
    )
    description = models.CharField(
        max_length=200,
        blank=True,
    )
    config_ordered = models.BooleanField(
        null=False,
        blank=False,
        verbose_name="Configured Ordered",
        help_text="Whether or not the configuration order matters, such as in ACLs.",
    )
    match_config = models.TextField(
        null=True,
        blank=True,
        verbose_name="Config to Match",
        help_text="The config to match that is matched based on the parent most configuration. e.g. `router bgp` or `ntp`.",
    )
    config_type = models.CharField(
        max_length=20,
        default=ComplianceRuleTypeChoice.TYPE_CLI,
        choices=ComplianceRuleTypeChoice,
        help_text="Whether the config is in cli or json/structured format.",
    )

    csv_headers = ["platform", "feature", "description", "config_ordered", "match_config", "config_type"]

    def to_csv(self):
        """Indicates model fields to return as csv."""
        return (
            self.platform.slug,
            self.feature.name,
            self.description,
            self.config_ordered,
            self.match_config,
            self.config_type,
        )

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

    def get_absolute_url(self):
        """Absolute url for the ComplianceRule instance."""
        return reverse("plugins:nautobot_golden_config:compliancerule", args=[self.pk])

    def clean(self):
        """Verify that if cli, then match_config is set."""
        if self.config_type == ComplianceRuleTypeChoice.TYPE_CLI and not self.match_config:
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

    device = models.ForeignKey(to="dcim.Device", on_delete=models.CASCADE, help_text="The device", blank=False)
    rule = models.ForeignKey(to="ComplianceRule", on_delete=models.CASCADE, blank=False, related_name="rule")
    compliance = models.BooleanField(null=True, blank=True)
    actual = models.JSONField(blank=True, help_text="Actual Configuration for feature")
    intended = models.JSONField(blank=True, help_text="Intended Configuration for feature")
    missing = models.JSONField(blank=True, help_text="Configuration that should be on the device.")
    extra = models.JSONField(blank=True, help_text="Configuration that should not be on the device.")
    ordered = models.BooleanField(default=True)
    # Used for django-pivot, both compliance and compliance_int should be set.
    compliance_int = models.IntegerField(null=True, blank=True)

    csv_headers = ["Device Name", "Feature", "Compliance"]

    def get_absolute_url(self):
        """Return absolute URL for instance."""
        return reverse("plugins:nautobot_golden_config:configcompliance", args=[self.pk])

    def to_csv(self):
        """Indicates model fields to return as csv."""
        return (self.device.name, self.rule.feature.name, self.compliance)

    def to_objectchange(self, action, related_object=None, object_data_extra=None, object_data_exclude=None):
        """Remove actual and intended configuration from changelog."""
        if not object_data_exclude:
            object_data_exclude = ["actual", "intended"]
        return ObjectChange(
            changed_object=self,
            object_repr=str(self),
            action=action,
            object_data=serialize_object(self, extra=object_data_extra, exclude=object_data_exclude),
            object_data_v2=serialize_object_v2(self),
            related_object=related_object,
        )

    class Meta:
        """Set unique together fields for model."""

        ordering = ["device"]
        unique_together = ("device", "rule")

    def __str__(self):
        """String representation of a the compliance."""
        return f"{self.device} -> {self.rule} -> {self.compliance}"

    def save(self, *args, **kwargs):
        """The actual configuration compliance happens here, but the details for actual compliance job would be found in FUNC_MAPPER."""
        if self.rule.config_type == ComplianceRuleTypeChoice.TYPE_CUSTOM and not FUNC_MAPPER.get(
            ComplianceRuleTypeChoice.TYPE_CUSTOM
        ):
            raise ValidationError(
                "Custom type provided, but no `get_custom_compliance` config set, please contact system admin."
            )

        compliance_details = FUNC_MAPPER[self.rule.config_type](obj=self)
        if self.rule.config_type == ComplianceRuleTypeChoice.TYPE_CUSTOM:
            _verify_get_custom_compliance_data(compliance_details)

        self.compliance = compliance_details["compliance"]
        self.compliance_int = compliance_details["compliance_int"]
        self.ordered = compliance_details["ordered"]
        self.missing = compliance_details["missing"]
        self.extra = compliance_details["extra"]

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

    device = models.ForeignKey(
        to="dcim.Device",
        on_delete=models.CASCADE,
        help_text="device",
        blank=False,
    )
    backup_config = models.TextField(blank=True, help_text="Full backup config for device.")
    backup_last_attempt_date = models.DateTimeField(null=True)
    backup_last_success_date = models.DateTimeField(null=True)

    intended_config = models.TextField(blank=True, help_text="Intended config for the device.")
    intended_last_attempt_date = models.DateTimeField(null=True)
    intended_last_success_date = models.DateTimeField(null=True)

    compliance_config = models.TextField(blank=True, help_text="Full config diff for device.")
    compliance_last_attempt_date = models.DateTimeField(null=True)
    compliance_last_success_date = models.DateTimeField(null=True)

    csv_headers = [
        "Device Name",
        "backup attempt",
        "backup successful",
        "intended attempt",
        "intended successful",
        "compliance attempt",
        "compliance successful",
    ]

    def to_csv(self):
        """Indicates model fields to return as csv."""
        return (
            self.device,
            self.backup_last_attempt_date,
            self.backup_last_success_date,
            self.intended_last_attempt_date,
            self.intended_last_success_date,
            self.compliance_last_attempt_date,
            self.compliance_last_success_date,
        )

    def to_objectchange(self, action, related_object=None, object_data_extra=None, object_data_exclude=None):
        """Remove actual and intended configuration from changelog."""
        if not object_data_exclude:
            object_data_exclude = ["backup_config", "intended_config", "compliance_config"]
        return ObjectChange(
            changed_object=self,
            object_repr=str(self),
            action=action,
            object_data=serialize_object(self, extra=object_data_extra, exclude=object_data_exclude),
            object_data_v2=serialize_object_v2(self),
            related_object=related_object,
        )

    class Meta:
        """Set unique together fields for model."""

        ordering = ["device"]

    def __str__(self):
        """String representation of a the compliance."""
        return f"{self.device}"


@extras_features(
    "graphql",
)
class GoldenConfigSetting(PrimaryModel):  # pylint: disable=too-many-ancestors
    """GoldenConfigSetting Model defintion. This provides global configs instead of via configs.py."""

    name = models.CharField(max_length=100, unique=True, blank=False)
    slug = models.SlugField(max_length=100, unique=True, blank=False)
    weight = models.PositiveSmallIntegerField(default=1000, blank=False)
    description = models.CharField(
        max_length=200,
        blank=True,
    )
    backup_repository = models.ForeignKey(
        to="extras.GitRepository",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="backup_repository",
        limit_choices_to={"provided_contents__contains": "nautobot_golden_config.backupconfigs"},
    )
    backup_path_template = models.CharField(
        max_length=255,
        null=False,
        blank=True,
        verbose_name="Backup Path in Jinja Template Form",
        help_text="The Jinja path representation of where the backup file will be found. The variable `obj` is available as the device instance object of a given device, as is the case for all Jinja templates. e.g. `{{obj.site.slug}}/{{obj.name}}.cfg`",
    )
    intended_repository = models.ForeignKey(
        to="extras.GitRepository",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="intended_repository",
        limit_choices_to={"provided_contents__contains": "nautobot_golden_config.intendedconfigs"},
    )
    intended_path_template = models.CharField(
        max_length=255,
        null=False,
        blank=True,
        verbose_name="Intended Path in Jinja Template Form",
        help_text="The Jinja path representation of where the generated file will be places. e.g. `{{obj.site.slug}}/{{obj.name}}.cfg`",
    )
    jinja_repository = models.ForeignKey(
        to="extras.GitRepository",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="jinja_template",
        limit_choices_to={"provided_contents__contains": "nautobot_golden_config.jinjatemplate"},
    )
    jinja_path_template = models.CharField(
        max_length=255,
        null=False,
        blank=True,
        verbose_name="Template Path in Jinja Template Form",
        help_text="The Jinja path representation of where the Jinja template can be found. e.g. `{{obj.platform.slug}}.j2`",
    )
    backup_test_connectivity = models.BooleanField(
        null=False,
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

    def get_absolute_url(self):  # pylint: disable=no-self-use
        """Return absolute URL for instance."""
        return reverse("plugins:nautobot_golden_config:goldenconfigsetting", args=[self.slug])

    def __str__(self):
        """Return a simple string if model is called."""
        return f"Golden Config Setting - {self.name}"

    @property
    def scope(self):
        """Returns filter from DynamicGroup."""
        if self.dynamic_group:
            return self.dynamic_group.filter
        return {}

    @scope.setter
    def scope(self, value):
        """Create DynamicGroup based on original scope JSON data."""
        if hasattr(self, "dynamic_group"):
            self.dynamic_group.filter = value
            self.dynamic_group.validated_save()
        else:
            name = f"GoldenConfigSetting {self.name} scope"
            content_type = ContentType.objects.get(app_label="dcim", model="device")
            dynamic_group = DynamicGroup.objects.create(
                name=name,
                slug=slugify(name),
                filter=value,
                content_type=content_type,
                description="Automatically generated for nautobot_golden_config GoldenConfigSetting.",
            )
            self.dynamic_group = dynamic_group
            self.validated_save()

    class Meta:
        """Set unique fields for model.

        Provide ordering used in tables and get_device_to_settings_map.
        Sorting on weight is performed from the highest weight value to the lowest weight value.
        This is to ensure only one plugin settings could be applied per single device based on priority and name.
        """

        verbose_name = "Golden Config Setting"
        ordering = ["-weight", "name"]  # Refer to weight comment in class docstring.

    def clean(self):
        """Validate the scope and GraphQL query."""
        super().clean()

        if self.sot_agg_query:
            LOGGER.debug("GraphQL - test  query start with: `%s`", GRAPHQL_STR_START)
            if not str(self.sot_agg_query.query).startswith(GRAPHQL_STR_START):
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
    """ConfigRemove for Regex Line Removals from Backup Configuration Model defintion."""

    name = models.CharField(max_length=255, null=False, blank=False)
    platform = models.ForeignKey(
        to="dcim.Platform",
        on_delete=models.CASCADE,
        related_name="backup_line_remove",
        null=False,
        blank=False,
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
    csv_headers = ["name", "platform", "description", "regex"]

    def to_csv(self):
        """Indicates model fields to return as csv."""
        return (self.name, self.platform.slug, self.regex)

    class Meta:
        """Meta information for ConfigRemove model."""

        ordering = ("platform", "name")
        unique_together = ("name", "platform")

    def __str__(self):
        """Return a simple string if model is called."""
        return self.name

    def get_absolute_url(self):  # pylint: disable=no-self-use
        """Return absolute URL for instance."""
        return reverse("plugins:nautobot_golden_config:configremove", args=[self.pk])


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
    """ConfigReplace for Regex Line Replacements from Backup Configuration Model defintion."""

    name = models.CharField(max_length=255, null=False, blank=False)
    platform = models.ForeignKey(
        to="dcim.Platform",
        on_delete=models.CASCADE,
        related_name="backup_line_replace",
        null=False,
        blank=False,
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
    csv_headers = ["name", "platform", "description", "regex", "replace"]

    def to_csv(self):
        """Indicates model fields to return as csv."""
        return (self.name, self.platform.slug, self.description, self.regex, self.replace)

    class Meta:
        """Meta information for ConfigReplace model."""

        ordering = ("platform", "name")
        unique_together = ("name", "platform")

    def get_absolute_url(self):
        """Return absolute URL for instance."""
        return reverse("plugins:nautobot_golden_config:configreplace", args=[self.pk])

    def __str__(self):
        """Return a simple string if model is called."""
        return self.name
