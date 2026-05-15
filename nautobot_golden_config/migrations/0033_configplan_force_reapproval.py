"""Force re-approval of existing ConfigPlans that have not yet been deployed.

Any ConfigPlan with status `Approved`, `Not Approved`, or no status is treated as
"not yet deployed" and gets a fresh `Pending` ApprovalWorkflow attached to the
default ConfigPlan workflow definition seeded by 0032. Their status is then nulled
so the `Approved` / `Not Approved` Status records can be cleaned up later. Plans
in `In Progress`, `Completed`, or `Failed` are left untouched.
"""

from django.db import migrations

WORKFLOW_NAME = "Config Plan Approval"
PENDING = "Pending"


def force_reapproval(apps, schema_editor):
    ConfigPlan = apps.get_model("nautobot_golden_config", "ConfigPlan")
    ApprovalWorkflow = apps.get_model("extras", "ApprovalWorkflow")
    ApprovalWorkflowStage = apps.get_model("extras", "ApprovalWorkflowStage")
    ApprovalWorkflowDefinition = apps.get_model("extras", "ApprovalWorkflowDefinition")
    ContentType = apps.get_model("contenttypes", "ContentType")

    try:
        workflow_def = ApprovalWorkflowDefinition.objects.get(name=WORKFLOW_NAME)
    except ApprovalWorkflowDefinition.DoesNotExist:
        # Admin removed the seeded definition before the migration ran; nothing to gate against.
        return

    stage_defs = list(workflow_def.approval_workflow_stage_definitions.all())
    ct_configplan = ContentType.objects.get_for_model(ConfigPlan)

    plans = ConfigPlan.objects.filter(status__name__in=["Approved", "Not Approved"]) | ConfigPlan.objects.filter(
        status__isnull=True
    )
    plans = plans.distinct()

    for plan in plans.iterator():
        workflow = ApprovalWorkflow.objects.create(
            approval_workflow_definition=workflow_def,
            object_under_review_content_type=ct_configplan,
            object_under_review_object_id=plan.pk,
            current_state=PENDING,
            user_name="",
        )
        ApprovalWorkflowStage.objects.bulk_create(
            [
                ApprovalWorkflowStage(
                    approval_workflow=workflow,
                    approval_workflow_stage_definition=stage_def,
                    state=PENDING,
                )
                for stage_def in stage_defs
            ]
        )

    plans.update(status=None)


def reverse_force_reapproval(apps, schema_editor):
    """Best-effort reversal: drop the workflows we attached and re-apply `Not Approved` to plans without status.

    Note: plans that were previously `Approved` cannot be distinguished from those that were
    `Not Approved` after this migration runs (both end up with status=None), so the reverse
    restores them all to `Not Approved`. This is acceptable because deployment is gated by
    workflow state, not status, and a downgrade would require the `Not Approved` Status
    record to exist (re-created by the reverse of 0034 if applicable).
    """
    ConfigPlan = apps.get_model("nautobot_golden_config", "ConfigPlan")
    ApprovalWorkflow = apps.get_model("extras", "ApprovalWorkflow")
    ApprovalWorkflowDefinition = apps.get_model("extras", "ApprovalWorkflowDefinition")
    ContentType = apps.get_model("contenttypes", "ContentType")
    Status = apps.get_model("extras", "Status")

    ct_configplan = ContentType.objects.get_for_model(ConfigPlan)

    try:
        workflow_def = ApprovalWorkflowDefinition.objects.get(name=WORKFLOW_NAME)
    except ApprovalWorkflowDefinition.DoesNotExist:
        workflow_def = None

    if workflow_def is not None:
        ApprovalWorkflow.objects.filter(
            approval_workflow_definition=workflow_def,
            object_under_review_content_type=ct_configplan,
        ).delete()

    try:
        not_approved = Status.objects.get(name="Not Approved")
    except Status.DoesNotExist:
        return

    ConfigPlan.objects.filter(status__isnull=True).update(status=not_approved)


class Migration(migrations.Migration):
    dependencies = [
        ("nautobot_golden_config", "0032_approval_workflow_seed_data"),
    ]

    operations = [
        migrations.RunPython(force_reapproval, reverse_force_reapproval),
    ]
