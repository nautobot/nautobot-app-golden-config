"""Django Models for tracking the configuration compliance per feature and device."""

import logging

from django.db import models
from django.core.exceptions import ValidationError
from django.shortcuts import reverse
from graphene_django.settings import graphene_settings
from graphql import get_default_backend
from graphql.error import GraphQLSyntaxError

from nautobot.core.models import BaseModel

LOGGER = logging.getLogger(__name__)


class ConfigCompliance(BaseModel):
    """Configuration compliance details."""

    device = models.ForeignKey(to="dcim.Device", on_delete=models.CASCADE, help_text="The device", blank=False)

    feature = models.CharField(max_length=32)
    compliance = models.BooleanField(null=True)
    actual = models.TextField(blank=True, help_text="Actual Configuration for feature")
    intended = models.TextField(blank=True, help_text="Intended Configuration for feature")
    missing = models.TextField(blank=True, help_text="Configuration that should be on the device.")
    extra = models.TextField(blank=True, help_text="Configuration that should not be on the device.")
    ordered = models.BooleanField(default=True)

    csv_headers = ["Device Name", "Feature", "Compliance"]

    def to_csv(self):
        """Indicates model fields to return as csv."""
        return self.device.name, self.feature, self.compliance

    class Meta:
        """Set unique together fields for model."""

        unique_together = (
            "device",
            "feature",
        )

    def __str__(self):
        """String representation of a the compliance."""
        return f"{self.device} -> {self.feature} -> {self.compliance}"


class GoldenConfiguration(BaseModel):
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

    def __str__(self):
        """String representation of a the compliance."""
        return f"{self.device}"


class ComplianceFeature(BaseModel):
    """Configuration compliance details."""

    name = models.CharField(max_length=255, null=False, blank=False)
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
        help_text="Whether or not the configuration is ordered determentistically.",
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


class GoldenConfigSettings(BaseModel):
    """GoldenConfigSettings Model defintion. This provides global configs instead of via configs.py."""

    backup_path_template = models.CharField(
        max_length=255,
        null=False,
        blank=True,
        verbose_name="Backup Path in Jinja Template Form",
        help_text="The Jinja path representation of where the backup file will be found. The variable `obj` is availiable as the device instance object of a given device, as is the case for all Jinja templates. e.g. `{{obj.site.slug}}/{{obj.name}}.cfg`",
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
        help_text="The Jinja path representation of where the Jinja temaplte can be found. e.g. `{{obj.platform.slug}}.j2`",
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
    remove_lines = models.TextField(
        null=False,
        blank=True,
        verbose_name="Lines to remove from backup config",
        help_text="Configuration lines to remove that match these patterns, one pattern per line.",
    )
    substitute_lines = models.TextField(
        null=False,
        blank=True,
        verbose_name="Lines to substitute from backup config",
        help_text="Lines substitute, using a regex pattern with replacement config three pipes (|||) and a regex pattern with a capture group. e.g. `redacted_config|||username\s+\S+\spassword\s+5\s+(\S+)\s+role\s+\S+`",  # pylint: disable=anomalous-backslash-in-string
    )

    def __str__(self):
        """Return a simple string if model is called."""
        return "Settings"

    def clean(self):
        """Validate there is only one model and if there is a GraphQL query, that it is valid."""
        if str(self.pk) != "aaaaaaaa-0000-0000-0000-000000000001":
            raise ValidationError("Only one entry with pk aaaaaaaa-0000-0000-0000-000000000001 is permitted")

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
