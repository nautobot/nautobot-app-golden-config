from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("nautobot_golden_config", "0010_multiple_gc_settings_part_2"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="goldenconfigsetting",
            name="backup_repository",
        ),
        migrations.RemoveField(
            model_name="goldenconfigsetting",
            name="intended_repository",
        ),
        migrations.AddField(
            model_name="goldenconfigsetting",
            name="backup_repository",
            field=models.ForeignKey(
                blank=True,
                limit_choices_to={"provided_contents__contains": "nautobot_golden_config.backupconfigs"},
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="backup_repository",
                to="extras.gitrepository",
            ),
        ),
        migrations.AddField(
            model_name="goldenconfigsetting",
            name="intended_repository",
            field=models.ForeignKey(
                blank=True,
                limit_choices_to={"provided_contents__contains": "nautobot_golden_config.intendedconfigs"},
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="intended_repository",
                to="extras.gitrepository",
            ),
        ),
    ]
