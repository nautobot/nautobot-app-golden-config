"""Functions to support config plan."""

from django.db.models import Q
from django.template import engines
from nautobot.apps.choices import ApprovalWorkflowStateChoices
from nautobot.core.utils.data import render_jinja2
from nautobot.dcim.models import Device
from nautobot.extras.models import Status

from nautobot_golden_config.models import ComplianceFeature
from nautobot_golden_config.utilities.constant import DEFAULT_DEPLOY_STATUS, PENDING_APPROVAL_STATUS
from nautobot_golden_config.utilities.helper import get_django_env


def config_plan_default_status():
    """Return the default status for config plan."""
    return Status.objects.get(name=DEFAULT_DEPLOY_STATUS)


def get_unapproved_config_plans(config_plan_qs):
    """Return the config plans in a queryset that are not yet approved for deployment.

    A plan with an approval workflow is approved only once that workflow is `Approved`; its status is just a
    mirror of the workflow. A plan without one is approved unless its status still says it is awaiting approval.

    Args:
        config_plan_qs (QuerySet): The `ConfigPlan` queryset to check.

    Returns:
        QuerySet: The plans that must not be deployed.
    """
    blocked_by_workflow = Q(
        associated_approval_workflows__current_state__in=[
            ApprovalWorkflowStateChoices.PENDING,
            ApprovalWorkflowStateChoices.DENIED,
            ApprovalWorkflowStateChoices.CANCELED,
        ]
    )
    blocked_by_status = Q(
        associated_approval_workflows__isnull=True,
        status__name__in=[DEFAULT_DEPLOY_STATUS, PENDING_APPROVAL_STATUS],
    )
    return config_plan_qs.filter(blocked_by_workflow | blocked_by_status).distinct()


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
    rendering_engine = engines["jinja"]
    rendering_engine.env = get_django_env()
    if context is None:
        context = {}
    context.update({"obj": device})
    return render_jinja2(template_code=commands, context=context)
