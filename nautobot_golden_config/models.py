"""Django Models for tracking the configuration compliance per feature and device."""

import logging

from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import validate_slug
from django.shortcuts import reverse
from graphene_django.settings import graphene_settings
from graphql import get_default_backend
from graphql.error import GraphQLSyntaxError

from nautobot.extras.models import ObjectChange
from nautobot.extras.utils import extras_features
from nautobot.utilities.utils import serialize_object
from nautobot.core.models.generics import PrimaryModel
from netutils.config.compliance import compliance

LOGGER = logging.getLogger(__name__)

def null_to_empty(val):
    """Convert to empty string if the value is currently null."""
    if not val:
        return ""
    return val

@extras_features(
    "custom_fields",
    "custom_links",
    "custom_validators",
    "export_templates",
    "graphql",
    "relationships",
    "statuses",
    "webhooks",
)
class ConfigCompliance(PrimaryModel):
    """Configuration compliance details."""

    device = models.ForeignKey(to="dcim.Device", on_delete=models.CASCADE, help_text="The device", blank=False)
    name = models.CharField(max_length=32, validators=[validate_slug])
    compliance = models.BooleanField(null=True)
    actual = models.TextField(blank=True, help_text="Actual Configuration for feature")
    intended = models.TextField(blank=True, help_text="Intended Configuration for feature")
    missing = models.TextField(blank=True, help_text="Configuration that should be on the device.")
    extra = models.TextField(blank=True, help_text="Configuration that should not be on the device.")
    ordered = models.BooleanField(default=True)

    csv_headers = ["Device Name", "Feature", "Compliance"]

    def get_absolute_url(self):
        """Return absolute URL for instance."""
        return reverse("plugins:nautobot_golden_config:configcompliance", args=[self.pk])

    def to_csv(self):
        """Indicates model fields to return as csv."""
        return (self.device.name, self.name, self.name, self.compliance)

    def to_objectchange(self, action):
        """Remove actual and intended configuration from changelog."""
        return ObjectChange(
            changed_object=self,
            object_repr=str(self),
            action=action,
            object_data=serialize_object(self, exclude=["actual", "intended"]),
        )

    class Meta:
        """Set unique together fields for model."""

        ordering = ["device"]
        unique_together = ("device", "name")

    def __str__(self):
        """String representation of a the compliance."""
        return f"{self.device} -> {self.name} -> {self.compliance}"

    def save(self, *args, **kwargs):
        """Overloading save to call full_clean that invokes clean."""
        self.full_clean()
        super().save(*args, **kwargs)

    def clean(self):
        """Ensures a secret is not leaked into the database object."""
        self.reordered_list_items = {}
        obj = ComplianceFeature.objects.get(platform=self.device.platform, name=self.name)
        features = [{"ordered": obj.config_ordered, "name": obj.name, "section": obj.match_config.splitlines()}]
        value = compliance(features, self.actual, self.intended, self.device.platform.slug, cfg_type="string")[self.name]
        self.compliance = value["compliant"]
        self.ordered: value["ordered_compliant"]
        self.missing =  null_to_empty(value["missing"])
        self.extra = null_to_empty(value["extra"])


@extras_features(
    "custom_validators",
    "export_templates",
    "graphql",
    "relationships",
    "statuses",
    "webhooks",
)
class GoldenConfiguration(PrimaryModel):
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

    def to_objectchange(self, action):
        """Remove actual and intended configuration from changelog."""
        return ObjectChange(
            changed_object=self,
            object_repr=str(self),
            action=action,
            object_data=serialize_object(self, exclude=["backup_config", "intended_config", "compliance_config"]),
        )

    class Meta:
        """Set unique together fields for model."""

        ordering = ["device"]

    def __str__(self):
        """String representation of a the compliance."""
        return f"{self.device}"


@extras_features(
    "custom_fields",
    "custom_validators",
    "export_templates",
    "graphql",
    "webhooks",
)
class ComplianceFeature(PrimaryModel):
    """Configuration compliance details."""

    name = models.CharField(max_length=255, null=False, blank=False, validators=[validate_slug])
    platform = models.ForeignKey(
        to="dcim.Platform",
        on_delete=models.CASCADE,
        related_name="compliance_features",
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
        null=False,
        blank=False,
        verbose_name="Config to Match",
        help_text="The config to match that is matched based on the parent most configuration. e.g. `router bgp` or `ntp`.",
    )

    class Meta:
        """Meta information for ComplianceFeature model."""

        ordering = ("name", "platform")
        unique_together = (
            "name",
            "platform",
        )

    def __str__(self):
        """Return a sane string representation of the instance."""
        return f"{self.platform} - {self.name}"

    def get_absolute_url(self):  # pylint: disable=no-self-use
        """Absolute url for the Compliance instance."""
        return reverse("plugins:nautobot_golden_config:compliancefeature_list")


class GoldenConfigSettings(PrimaryModel):
    """GoldenConfigSettings Model defintion. This provides global configs instead of via configs.py."""

    backup_path_template = models.CharField(
        max_length=255,
        null=False,
        blank=True,
        verbose_name="Backup Path in Jinja Template Form",
        help_text="The Jinja path representation of where the backup file will be found. The variable `obj` is available as the device instance object of a given device, as is the case for all Jinja templates. e.g. `{{obj.site.slug}}/{{obj.name}}.cfg`",
    )
    intended_path_template = models.CharField(
        max_length=255,
        null=False,
        blank=True,
        verbose_name="Intended Path in Jinja Template Form",
        help_text="The Jinja path representation of where the generated file will be places. e.g. `{{obj.site.slug}}/{{obj.name}}.cfg`",
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
    shorten_sot_query = models.BooleanField(
        null=False,
        default=False,
        verbose_name="Shorten the SoT data returned",
        help_text="This will shorten the response from `devices[0]{data}` to `{data}`",
    )
    sot_agg_query = models.TextField(
        null=False,
        blank=True,
        verbose_name="GraphQL Query",
        help_text="A query that is evaluated and used to render the config. The query must start with `query ($device: String!)`.",
    )
    only_primary_ip = models.BooleanField(
        null=False,
        default=False,
        verbose_name="Include only devices with a Primary IP.",
    )
    exclude_chassis_members = models.BooleanField(
        null=False,
        default=False,
        verbose_name="Exclude non-master chassis members.",
        help_text="This will ensure that chassis that are connected to only via the chassis master.",
    )


    def get_absolute_url(self):  # pylint: disable=no-self-use
        """Return absolute URL for instance."""
        return reverse("plugins:nautobot_golden_config:goldenconfigsettings")

    def __str__(self):
        """Return a simple string if model is called."""
        return "Golden Config Settings"

    def delete(self, *args, **kwargs):
        """Enforce the singleton pattern, there is no way to delete the configurations."""

    @classmethod
    def load(cls):
        """Enforce the singleton pattern, fail it somehow more than one instance."""
        if len(cls.objects.all()) != 1:
            raise ValidationError("There was an error where more than one instance existed for a setting.")
        return cls.objects.first()

    def clean(self):
        """Validate there is only one model and if there is a GraphQL query, that it is valid."""
        super().clean()

        if self.sot_agg_query:
            try:
                LOGGER.debug("GraphQL - test query: `%s`", str(self.sot_agg_query))
                backend = get_default_backend()
                schema = graphene_settings.SCHEMA
                backend.document_from_string(schema, str(self.sot_agg_query))
            except GraphQLSyntaxError as error:
                raise ValidationError(str(error))  # pylint: disable=raise-missing-from
            graphql_start = "query ($device: String!)"
            if not str(self.sot_agg_query).startswith(graphql_start):
                raise ValidationError(f"The GraphQL query must start with exactly `{graphql_start}`")


class ConfigRemove(PrimaryModel):
    """GoldenConfigSettings for Regex Line Removals from Backup Configuration Model defintion."""

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
    regex_line = models.CharField(
        max_length=200,
        verbose_name="Regex Pattern",
        help_text="Regex pattern used to remove a line from the backup configuration.",
    )
    csv_headers = ["name", "platform", "description", "regex_line"]

    class Meta:
        """Meta information for ComplianceFeature model."""

        ordering = ("platform", "name")
        unique_together = ("name", "platform")

    def __str__(self):
        """Return a simple string if model is called."""
        return self.name

    def get_absolute_url(self):  # pylint: disable=no-self-use
        """Return absolute URL for instance."""
        # TODO: Update to create detailed view, as shown in next line
        # return reverse("plugins:nautobot_golden_config:configremove", args=[self.pk])
        return reverse(
            "plugins:nautobot_golden_config:configremove_list",
        )


class ConfigReplace(PrimaryModel):
    """GoldenConfigSettings for Regex Line Replacements from Backup Configuration Model defintion."""

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
    substitute_text = models.CharField(
        max_length=200,
        verbose_name="Regex Pattern to Substitute",
        help_text="Regex pattern that will be found and replaced with 'replaced text'.",
    )
    replaced_text = models.CharField(
        max_length=200,
        verbose_name="Replaced Text",
        help_text="Text that will be inserted in place of Regex pattern match.",
    )

    csv_headers = ["name", "platform", "description", "substitute_text", "replaced_text"]

    class Meta:
        """Meta information for ComplianceFeature model."""

        ordering = ("platform", "name")
        unique_together = ("name", "platform")

    def get_absolute_url(self):  # pylint: disable=no-self-use
        """Return absolute URL for instance."""
        # TODO: Update to create detailed view, as shown in next line
        # return reverse("plugins:nautobot_golden_config:configreplace", args=[self.pk])
        return reverse(
            "plugins:nautobot_golden_config:configreplace_list",
        )

    def __str__(self):
        """Return a simple string if model is called."""
        return self.name
