"""Choicesets for golden config."""
from nautobot.core.choices import ChoiceSet


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


class DynamicRemediationExpressionChoice(ChoiceSet):
    """Choiceset used for Dynamic Remediation Expression Choices."""

    STARTS_WITH = "startswith"
    ENDS_WITH = "endswith"
    EQUALS = "equals"
    CONTAINS = "contains"

    CHOICES = (
        (STARTS_WITH, "startswith"),
        (ENDS_WITH, "endswith"),
        (EQUALS, "equals"),
        (CONTAINS, "contains"),
    )
