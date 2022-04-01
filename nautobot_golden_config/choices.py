"""Choicesets for golden config."""
from nautobot.utilities.choices import ChoiceSet


class ComplianceRuleTypeChoice(ChoiceSet):
    """Choiceset used by ComplianceRule."""

    TYPE_CLI = "cli"
    TYPE_JSON = "json"
    TYPE_CUSTOM = "custom"

    CHOICES = (
        (TYPE_CLI, "CLI"),
        (TYPE_JSON, "JSON"),
        (TYPE_CUSTOM, "CUSTOM"),
    )
