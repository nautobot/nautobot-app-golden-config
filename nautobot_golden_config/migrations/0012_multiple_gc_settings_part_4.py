from django.db import migrations


def convert_many_repos_part2(apps, schema_editor):
    """
    Add the current `backup_repository_tmp` and `intended_repository_tmp` object values
    to the FKs final attributes to retain data.`
    """
    GoldenConfigSetting = apps.get_model("nautobot_golden_config", "GoldenConfigSetting")

    settings_obj = GoldenConfigSetting.objects.first()

    if settings_obj.backup_repository_tmp:
        settings_obj.backup_repository = settings_obj.backup_repository_tmp
        settings_obj.save()

    if settings_obj.intended_repository_tmp:
        settings_obj.intended_repository = settings_obj.intended_repository_tmp
        settings_obj.save()


class Migration(migrations.Migration):
    dependencies = [
        ("nautobot_golden_config", "0011_multiple_gc_settings_part_3"),
    ]

    operations = [
        migrations.RunPython(convert_many_repos_part2),
    ]
