from django.db import migrations, models
import json


def jsonify(apps, schedma_editor):
    """Converts textfield to json in preparation for migration."""
    ConfigCompliance = apps.get_model("nautobot_golden_config", "ConfigCompliance")
    queryset = ConfigCompliance.objects.all()
    attrs = ["actual", "extra", "intended", "missing"]
    for i in queryset:
        for attr in attrs:
            value = getattr(i, attr)
            if value:
                setattr(i, attr, json.dumps(value))
        i.save()


class Migration(migrations.Migration):
    dependencies = [
        ("nautobot_golden_config", "0004_auto_20210616_2234"),
    ]

    operations = [
        migrations.RunPython(code=jsonify),
        migrations.AlterField(
            model_name="compliancerule",
            name="match_config",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="configcompliance",
            name="actual",
            field=models.JSONField(blank=True),
        ),
        migrations.AlterField(
            model_name="configcompliance",
            name="extra",
            field=models.JSONField(blank=True),
        ),
        migrations.AlterField(
            model_name="configcompliance",
            name="intended",
            field=models.JSONField(blank=True),
        ),
        migrations.AlterField(
            model_name="configcompliance",
            name="missing",
            field=models.JSONField(blank=True),
        ),
    ]
