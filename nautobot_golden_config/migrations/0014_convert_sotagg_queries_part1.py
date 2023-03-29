from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("extras", "0018_joblog_data_migration"),
        ("nautobot_golden_config", "0013_multiple_gc_settings_part_5"),
    ]

    operations = [
        migrations.AddField(
            model_name="goldenconfigsetting",
            name="sot_agg_query_tmp",
            field=models.TextField(blank=True),
        ),
    ]
