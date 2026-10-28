import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("extras", "0127_approval_workflow_models"),
        ("nautobot_golden_config", "0031_alter_configplan_change_control_url"),
    ]

    operations = [
        migrations.AddField(
            model_name="goldenconfigsetting",
            name="config_plan_approval_workflow",
            field=models.ForeignKey(
                blank=True,
                help_text="Approval Workflow Definition started for each Config Plan generated for devices in this setting's scope. When empty, Config Plan approval is tracked with the Config Plan status.",
                limit_choices_to={
                    "model_content_type__app_label": "nautobot_golden_config",
                    "model_content_type__model": "configplan",
                },
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="golden_config_settings",
                to="extras.approvalworkflowdefinition",
            ),
        ),
    ]
