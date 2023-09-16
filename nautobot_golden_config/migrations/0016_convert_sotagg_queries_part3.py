import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("nautobot_golden_config", "0015_convert_sotagg_queries_part2"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="goldenconfigsetting",
            name="sot_agg_query",
        ),
        migrations.AddField(
            model_name="goldenconfigsetting",
            name="sot_agg_query",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="sot_aggregation",
                to="extras.graphqlquery",
            ),
        ),
    ]
