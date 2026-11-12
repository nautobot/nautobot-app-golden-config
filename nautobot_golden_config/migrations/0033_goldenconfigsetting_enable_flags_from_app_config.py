from django.conf import settings
from django.db import migrations

# The app-level `enable_*` settings this migration retires, mapped to the value each one took when unset.
APP_LEVEL_DEFAULTS = {
    "enable_backup": True,
    "enable_compliance": True,
    "enable_intended": True,
    "enable_sotagg": True,
    "enable_plan": True,
    "enable_deploy": True,
    "enable_postprocessing": False,
}


def copy_enable_flags_from_app_config(apps, schema_editor):
    """Carry the app-level `enable_*` settings onto every existing GoldenConfigSetting."""
    GoldenConfigSetting = apps.get_model("nautobot_golden_config", "GoldenConfigSetting")
    app_config = settings.PLUGINS_CONFIG.get("nautobot_golden_config", {})
    flags = {name: bool(app_config.get(name, default)) for name, default in APP_LEVEL_DEFAULTS.items()}
    GoldenConfigSetting.objects.using(schema_editor.connection.alias).update(**flags)


class Migration(migrations.Migration):
    dependencies = [
        ("nautobot_golden_config", "0032_goldenconfigsetting_enable_backup_and_more"),
    ]

    operations = [
        migrations.RunPython(copy_enable_flags_from_app_config, migrations.RunPython.noop),
    ]
