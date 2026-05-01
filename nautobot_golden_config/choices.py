"""Choicesets for golden config."""

from nautobot.apps.choices import ChoiceSet


class ComplianceRuleConfigTypeChoice(ChoiceSet):
    """Choiceset used by ComplianceRule."""

    TYPE_CLI = "cli"
    TYPE_JSON = "json"
    TYPE_XML = "xml"

    CHOICES = (
        (TYPE_CLI, "CLI"),
        (TYPE_JSON, "JSON"),
        (TYPE_XML, "XML"),
    )


class RemediationTypeChoice(ChoiceSet):
    """Choiceset used by RemediationSetting."""

    TYPE_HIERCONFIG = "hierconfig"
    TYPE_CUSTOM = "custom_remediation"

    CHOICES = (
        (TYPE_HIERCONFIG, "HIERCONFIG"),
        (TYPE_CUSTOM, "CUSTOM_REMEDIATION"),
    )


class EmptyComplianceBehaviorChoice(ChoiceSet):
    """Choiceset for how to handle compliance when configurations are empty."""

    TYPE_VALIDATED = "validated"
    TYPE_EMPTY_BOTH = "empty_both"
    TYPE_EMPTY_INTENDED = "empty_intended"

    CHOICES = (
        (TYPE_VALIDATED, "Validated"),
        (TYPE_EMPTY_BOTH, "Empty Both"),
        (TYPE_EMPTY_INTENDED, "Empty Intended"),
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
