# Generated by Django 3.2.16 on 2023-07-07 09:21

import django.core.serializers.json
from django.db import migrations, models
import django.db.models.deletion
import nautobot.extras.models.mixins
import taggit.managers
import uuid

def add_remediation_field_if_not_exists(apps, schema_editor):
    """
    Add Remediation Field to ConfigCompliance model if it was not added before by 0005.
    """
    ConfigCompliance = apps.get_model('nautobot_golden_config', 'ConfigCompliance')

    # Check if the field already exists in the database
    if not ConfigCompliance._meta.get_field('remediation'):
        # If the field does not exist, add it using the migrations.AddField operation
        migrations.AddField(
            model_name="configcompliance",
            name="remediation",
            field=models.JSONField(blank=True, null=True),
        )

class Migration(migrations.Migration):
    dependencies = [
        ("dcim", "0019_device_redundancy_group_data_migration"),
        ("extras", "0053_relationship_required_on"),
        ("nautobot_golden_config", "0024_convert_custom_compliance_rules"),
    ]

    operations = [
        migrations.RunPython(add_remediation_field_if_not_exists),
        migrations.AddField(
            model_name="compliancerule",
            name="config_remediation",
            field=models.BooleanField(default=False),
        ),
        migrations.CreateModel(
            name="RemediationSetting",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True
                    ),
                ),
                ("created", models.DateField(auto_now_add=True, null=True)),
                ("last_updated", models.DateTimeField(auto_now=True, null=True)),
                (
                    "_custom_field_data",
                    models.JSONField(blank=True, default=dict, encoder=django.core.serializers.json.DjangoJSONEncoder),
                ),
                ("remediation_type", models.CharField(default="hierconfig", max_length=50)),
                ("remediation_options", models.JSONField(blank=True, default=dict)),
                (
                    "platform",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="remediation_settings",
                        to="dcim.platform",
                    ),
                ),
                ("tags", taggit.managers.TaggableManager(through="extras.TaggedItem", to="extras.Tag")),
            ],
            options={
                "abstract": False,
            },
            bases=(
                models.Model,
                nautobot.extras.models.mixins.DynamicGroupMixin,
                nautobot.extras.models.mixins.NotesMixin,
            ),
        ),
    ]
