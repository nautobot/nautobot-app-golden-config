"""Seed the default ApprovalWorkflow definition and architect/approver/operator groups for ConfigPlan."""

from django.db import migrations

ARCHITECT_GROUP = "nautobot-default-configplan-architect"
APPROVER_GROUP = "nautobot-default-configplan-approver"
OPERATOR_GROUP = "nautobot-default-configplan-operator"

WORKFLOW_NAME = "Config Plan Approval"
STAGE_NAME = "Approval by nautobot-default-configplan-approver"

ARCHITECT_PERMS = "nautobot-default-configplan-architect-permissions"
APPROVER_PERMS = "nautobot-default-configplan-approver-permissions"
OPERATOR_PERMS = "nautobot-default-configplan-operator-permissions"


def create_default_configplan_workflow(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    ObjectPermission = apps.get_model("users", "ObjectPermission")
    ApprovalWorkflow = apps.get_model("extras", "ApprovalWorkflow")
    ApprovalWorkflowStage = apps.get_model("extras", "ApprovalWorkflowStage")
    ApprovalWorkflowStageResponse = apps.get_model("extras", "ApprovalWorkflowStageResponse")
    ApprovalWorkflowDefinition = apps.get_model("extras", "ApprovalWorkflowDefinition")
    ApprovalWorkflowStageDefinition = apps.get_model("extras", "ApprovalWorkflowStageDefinition")
    ContentType = apps.get_model("contenttypes", "ContentType")
    ConfigPlan = apps.get_model("nautobot_golden_config", "ConfigPlan")

    groups = {
        ARCHITECT_GROUP: Group.objects.get_or_create(name=ARCHITECT_GROUP)[0],
        APPROVER_GROUP: Group.objects.get_or_create(name=APPROVER_GROUP)[0],
        OPERATOR_GROUP: Group.objects.get_or_create(name=OPERATOR_GROUP)[0],
    }

    ct_workflow = ContentType.objects.get_for_model(ApprovalWorkflow)
    ct_stage = ContentType.objects.get_for_model(ApprovalWorkflowStage)
    ct_response = ContentType.objects.get_for_model(ApprovalWorkflowStageResponse)
    ct_workflow_def = ContentType.objects.get_for_model(ApprovalWorkflowDefinition)
    ct_stage_def = ContentType.objects.get_for_model(ApprovalWorkflowStageDefinition)
    ct_configplan = ContentType.objects.get_for_model(ConfigPlan)

    awf_def, _ = ApprovalWorkflowDefinition.objects.update_or_create(
        name=WORKFLOW_NAME,
        defaults={
            "model_content_type_id": ct_configplan.id,
            "model_constraints": {},
            "weight": 100,
        },
    )

    ApprovalWorkflowStageDefinition.objects.update_or_create(
        name=STAGE_NAME,
        defaults={
            "approval_workflow_definition": awf_def,
            "sequence": 10,
            "min_approvers": 1,
            "denial_message": "This Config Plan requires an approval from nautobot-default-configplan-approver.",
            "approver_group": groups[APPROVER_GROUP],
        },
    )

    perms_data = [
        {
            "name": ARCHITECT_PERMS,
            "description": "Golden Config: permissions aligned to the Workflow Architect persona for ConfigPlan.",
            "enabled": True,
            "actions": ["view", "add", "change", "delete"],
            "object_types": [ct_workflow_def.id, ct_stage_def.id],
            "groups": [groups[ARCHITECT_GROUP]],
        },
        {
            "name": APPROVER_PERMS,
            "description": "Golden Config: permissions aligned to the Workflow Approver persona for ConfigPlan.",
            "enabled": True,
            "actions": ["view", "change"],
            "object_types": [ct_stage.id],
            "groups": [groups[APPROVER_GROUP]],
        },
        {
            "name": OPERATOR_PERMS,
            "description": "Golden Config: permissions aligned to the Workflow Operator persona for ConfigPlan.",
            "enabled": True,
            "actions": ["view"],
            "object_types": [ct_workflow.id, ct_stage.id, ct_response.id],
            "groups": [
                groups[OPERATOR_GROUP],
                groups[APPROVER_GROUP],
                groups[ARCHITECT_GROUP],
            ],
        },
    ]

    for perm in perms_data:
        obj, _ = ObjectPermission.objects.update_or_create(
            name=perm["name"],
            defaults={
                "description": perm["description"],
                "enabled": perm["enabled"],
                "actions": perm["actions"],
            },
        )
        obj.object_types.set(perm["object_types"])
        obj.groups.set(perm["groups"])
        obj.save()


def reverse_default_configplan_workflow(apps, schema_editor):
    ObjectPermission = apps.get_model("users", "ObjectPermission")
    ApprovalWorkflowDefinition = apps.get_model("extras", "ApprovalWorkflowDefinition")

    ObjectPermission.objects.filter(name__in=[ARCHITECT_PERMS, APPROVER_PERMS, OPERATOR_PERMS]).delete()
    ApprovalWorkflowDefinition.objects.filter(name=WORKFLOW_NAME).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("nautobot_golden_config", "0031_alter_configplan_change_control_url"),
        ("extras", "0132_approval_workflow_seed_data"),
    ]

    operations = [
        migrations.RunPython(create_default_configplan_workflow, reverse_default_configplan_workflow),
    ]
