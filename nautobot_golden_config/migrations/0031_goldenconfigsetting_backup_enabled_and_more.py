# Generated by Django 4.2.17 on 2024-12-19 20:51

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("nautobot_golden_config", "0030_alter_goldenconfig_device"),
    ]

    operations = [
        migrations.AddField(
            model_name="goldenconfigsetting",
            name="backup_enabled",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="goldenconfigsetting",
            name="compliance_enabled",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="goldenconfigsetting",
            name="deploy_enabled",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="goldenconfigsetting",
            name="intended_enabled",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="goldenconfigsetting",
            name="plan_enabled",
            field=models.BooleanField(default=True),
        ),
    ]
