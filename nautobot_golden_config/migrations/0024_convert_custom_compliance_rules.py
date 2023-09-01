from django.db import migrations
from nautobot_golden_config.choices import ComplianceRuleConfigTypeChoice


def convert_custom_compliance_rules(apps, schema_editor):
    """
    Convert custom compliance rules by rewriting `config_type` if defined as `custom` to custom_compliance bool.
    All custom rules are to be rewritten into TYPE_CLI
    """
    ComplianceRule = apps.get_model("nautobot_golden_config", "ComplianceRule")

    compliance_rules = ComplianceRule.objects.filter(config_type="custom")

    for compliance_rule in compliance_rules:
        compliance_rule.config_type = ComplianceRuleConfigTypeChoice.TYPE_CLI
        compliance_rule.custom_compliance = True
        compliance_rule.save()


class Migration(migrations.Migration):
    dependencies = [
        ("nautobot_golden_config", "0023_alter_custom_compliance"),
    ]

    operations = [
        migrations.RunPython(convert_custom_compliance_rules),
    ]
