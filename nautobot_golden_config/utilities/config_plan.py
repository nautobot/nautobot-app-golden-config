"""Functions to support config plan."""
from django.contrib.contenttypes.models import ContentType

from nautobot.dcim.models import Device
from nautobot.extras.models import Status

from nautobot_golden_config.models import ConfigPlan, ComplianceFeature

# TODO: Make the default Status configurable
DEFAULT_STATUS = Status.objects.filter(
    content_types=ContentType.objects.get_for_model(ConfigPlan),
    slug="not-accepted",
).first()


def generate_config_plan_from_compliance_feature(
    device: Device,
    plan_type: str,
    feature: ComplianceFeature,
    change_control_id: str = None,
    status: Status = None,
):
    """Generate config plan from config compliance.

    Args:
        device (Device): Device to generate config plan for.
        plan_type (str): The ConfigCompliance attribute to pull from.
        feature (ComplianceFeature): The feature to generate config plan for.
        change_control_id (str, optional): The change control ID to use for the config plan.
        status (Status, optional): The status to use for the config plan.
    """
    # Grab the config compliance for the feature
    feature_compliance = device.configcompliance_set.filter(rule__feature=feature).first()
    # If the config compliance exists and has the plan type generated, create the config plan
    if feature_compliance and hasattr(feature_compliance, plan_type) and getattr(feature_compliance, plan_type):
        status = status or DEFAULT_STATUS
        return ConfigPlan.objects.create(
            plan_type=plan_type,
            device=device,
            config_set=getattr(feature_compliance, plan_type),
            feature=feature,
            change_control_id=change_control_id,
            status=status,
        )
    return ConfigPlan.objects.none()


def generate_config_plan_from_manual(
    device: Device,
    config_set: str,
    change_control_id: str = None,
    status: Status = None,
):
    """Generate config plan from manual config set.

    Args:
        device (Device): Device to generate config plan for.
        config_set (str): The config set for the generated config plan.
        change_control_id (str, optional): The change control ID to use for the config plan.
        status (Status, optional): The status to use for the config plan.
    """
    status = status or DEFAULT_STATUS
    return ConfigPlan.objects.create(
        plan_type="manual",
        device=device,
        config_set=config_set,
        change_control_id=change_control_id,
        status=status,
    )
