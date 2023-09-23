from django.db import migrations


def alter_fields(apps, schema_editor):
    """
    Save to the temp field the current SoTAgg Query strings.
    """
    ConfigCompliance = apps.get_model("nautobot_golden_config", "ConfigCompliance")

    for instance in ConfigCompliance.objects.all():
        if instance.compliance is None:
            instance.compliance = False
            instance.save()
        if instance.compliance_int is None:
            instance.compliance_int = 0
            instance.save()
        if instance.ordered is None:
            instance.ordered = False
            instance.save()
        if instance.remediation is None:
            instance.remediation = ""
            instance.save()

    ComplianceRule = apps.get_model("nautobot_golden_config", "ComplianceRule")

    for instance in ComplianceRule.objects.all():
        if instance.config_ordered is None:
            instance.config_ordered = False
            instance.save()
        if instance.match_config is None:
            instance.match_config = ""
            instance.save()


class Migration(migrations.Migration):
    dependencies = [
        ("extras", "0098_rename_data_jobresult_result"),
        ("nautobot_golden_config", "0027_auto_20230915_1657"),
    ]

    operations = [
        migrations.RunPython(alter_fields),
    ]
