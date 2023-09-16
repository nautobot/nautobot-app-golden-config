from django.db import migrations


def save_existing_sotagg_queries(apps, schema_editor):
    """
    Save to the temp field the current SoTAgg Query strings.
    """
    GoldenConfigSetting = apps.get_model("nautobot_golden_config", "GoldenConfigSetting")

    for gc_setting_obj in GoldenConfigSetting.objects.all():
        if gc_setting_obj.sot_agg_query:
            gc_setting_obj.sot_agg_query_tmp = gc_setting_obj.sot_agg_query
            gc_setting_obj.save()


class Migration(migrations.Migration):
    dependencies = [
        ("nautobot_golden_config", "0014_convert_sotagg_queries_part1"),
    ]

    operations = [
        migrations.RunPython(save_existing_sotagg_queries),
    ]
