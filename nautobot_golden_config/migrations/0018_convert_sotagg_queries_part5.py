from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("nautobot_golden_config", "0017_convert_sotagg_queries_part4"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="goldenconfigsetting",
            name="sot_agg_query_tmp",
        ),
    ]
