"""Choicesets for golden config."""
from nautobot.utilities.choices import ChoiceSet


class ComplianceRuleConfigTypeChoice(ChoiceSet):
    """Choiceset used by ComplianceRule."""

    TYPE_CLI = "cli"
    TYPE_JSON = "json"

    CHOICES = (
        (TYPE_CLI, "CLI"),
        (TYPE_JSON, "JSON"),
        (TYPE_CUSTOM, "CUSTOM"),
    )


class RemediationTypeChoice(ChoiceSet):
    """Choiceset used by RemediationSetting."""

    TYPE_HIERCONFIG = "hierconfig"
    TYPE_CUSTOM = "custom"

    CHOICES = (
        (TYPE_HIERCONFIG, "HIERCONFIG"),
        (TYPE_CUSTOM, "CUSTOM"),
    )


class ConfigPlanTypeChoice(ChoiceSet):
    """Choiceset used by ConfigPlan."""

    TYPE_FEATURE_INTENDED = "feature_intended"
    TYPE_FEATURE_MISSING = "feature_missing"
    TYPE_FEATURE_REMEDIATION = "feature_remediation"
    TYPE_FULL_REPLACE = "full_replace"
    TYPE_MANUAL = "manual"

    CHOICES = (
        (TYPE_FEATURE_INTENDED, "FEATURE_INTENDED"),
        (TYPE_FEATURE_MISSING, "FEATURE_MISSING"),
        (TYPE_FEATURE_REMEDIATION, "TYPE_FEATURE_REMEDIATION"),
        (TYPE_FULL_REPLACE, "FULL_REPLACE"),
        (TYPE_MANUAL, "MANUAL"),
    )
