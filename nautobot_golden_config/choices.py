"""Choicesets for golden config."""
from nautobot.utilities.choices import ChoiceSet


class ComplianceRuleConfigTypeChoice(ChoiceSet):
    """Choiceset used by ComplianceRule."""

    TYPE_CLI = "cli"
    TYPE_JSON = "json"

    CHOICES = (
        (TYPE_CLI, "CLI"),
        (TYPE_JSON, "JSON"),
    )


class RemediationTypeChoice(ChoiceSet):
    """Choiceset used by RemediationSetting."""

    TYPE_HIERCONFIG = "hierconfig"
    TYPE_CUSTOM = "custom_remediation"

    CHOICES = (
        (TYPE_HIERCONFIG, "HIERCONFIG"),
        (TYPE_CUSTOM, "CUSTOM_REMEDIATION"),
    )


class ConfigPlanTypeChoice(ChoiceSet):
    """Choiceset used by ConfigPlan."""

    TYPE_INTENDED = "intended"
    TYPE_MISSING = "missing"
    TYPE_REMEDIATION = "remediation"
    TYPE_MANUAL = "manual"

    CHOICES = (
        (TYPE_INTENDED, "Intended"),
        (TYPE_MISSING, "Missing"),
        (TYPE_REMEDIATION, "Remediation"),
        (TYPE_MANUAL, "Manual"),
    )
