"""Functions to support config plan."""
from nautobot.dcim.models import Device
from nautobot.extras.models import Status
from nautobot.utilities.utils import render_jinja2

from nautobot_golden_config.models import ComplianceFeature


# TODO: Make the default Status configurable
def config_plan_default_status():
    """Return the default status for config plan."""
    return Status.objects.filter(
        content_types__model="configplan",
        slug="not-approved",
    ).first()


def generate_config_set_from_compliance_feature(device: Device, plan_type: str, feature: ComplianceFeature):
    """Generate config set from config compliance.

    Args:
        device (Device): Device to generate config set for.
        plan_type (str): The ConfigCompliance attribute to pull from.
        feature (ComplianceFeature): The feature to generate config set for.
    """
    # Grab the config compliance for the feature
    feature_compliance = device.configcompliance_set.filter(rule__feature=feature).first()
    # If the config compliance exists and has the plan type generated, return the config set
    if feature_compliance and hasattr(feature_compliance, plan_type) and getattr(feature_compliance, plan_type):
        return getattr(feature_compliance, plan_type)
    return ""


def generate_config_set_from_manual(device: Device, commands: str, context: dict = None):
    """Generate config set from manual config set.

    Args:
        device (Device): Device to generate config set for.
        commands (str): The commands for the generated config set.
        context (dict, optional): The context to render the commands with.
    """
    if context is None:
        context = {}
    context.update({"obj": device})
    return render_jinja2(template_code=commands, context=context)
