"""Forms for nautobot_golden_config."""

from django import forms
from nautobot.apps.forms import NautobotBulkEditForm, NautobotFilterForm, NautobotModelForm, TagsBulkEditFormMixin

from nautobot_golden_config import models


class ComplianceFeatureForm(NautobotModelForm):  # pylint: disable=too-many-ancestors
    """ComplianceFeature creation/edit form."""

    class Meta:
        """Meta attributes."""

        model = models.ComplianceFeature
        fields = "__all__"


class ComplianceFeatureBulkEditForm(TagsBulkEditFormMixin, NautobotBulkEditForm):  # pylint: disable=too-many-ancestors
    """ComplianceFeature bulk edit form."""

    pk = forms.ModelMultipleChoiceField(queryset=models.ComplianceFeature.objects.all(), widget=forms.MultipleHiddenInput)
    description = forms.CharField(required=False)

    class Meta:
        """Meta attributes."""

        nullable_fields = [
            "description",
        ]


class ComplianceFeatureFilterForm(NautobotFilterForm):
    """Filter form to filter searches."""

    model = models.ComplianceFeature
    field_order = ["q", "name"]

    q = forms.CharField(
        required=False,
        label="Search",
        help_text="Search within Name.",
    )
    name = forms.CharField(required=False, label="Name")
