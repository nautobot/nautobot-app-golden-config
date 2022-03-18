from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("nautobot_golden_config", "0012_multiple_gc_settings_part_4"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="goldenconfigsetting",
            name="backup_repository_tmp",
        ),
        migrations.RemoveField(
            model_name="goldenconfigsetting",
            name="intended_repository_tmp",
        ),
    ]
