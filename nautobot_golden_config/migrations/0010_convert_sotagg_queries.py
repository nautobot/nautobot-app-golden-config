from datetime import date

from django.db import migrations, models
import django.db.models.deletion


def save_existing_sotagg_queries(apps, schema_editor):
    """
    Save to the temp field the current SoTAgg Query strings.
    """
    GoldenConfigSetting = apps.get_model("nautobot_golden_config", "GoldenConfigSetting")

    for gc_setting_obj in GoldenConfigSetting.objects.all():
        if gc_setting_obj.sot_agg_query:
            gc_setting_obj.sot_agg_query_tmp = gc_setting_obj.sot_agg_query
            gc_setting_obj.save()


def create_and_link_gql_queries(apps, schema_editor):
    """
    Create Saved GraphQL Query objects and link them to SoTAgg Query field.
    """
    GoldenConfigSetting = apps.get_model("nautobot_golden_config", "GoldenConfigSetting")
    GraphQLQuery = apps.get_model("extras", "GraphQLQuery")

    today = str(date.today())

    for gc_setting_obj in GoldenConfigSetting.objects.all():
        if gc_setting_obj.sot_agg_query_tmp:
            sotagg_name = gc_setting_obj.name
            sotagg_query = gc_setting_obj.sot_agg_query_tmp
            gqlsq_name = f"GC {sotagg_name} - {today}"

            gqlsq_obj = GraphQLQuery()
            gqlsq_obj.name = gqlsq_name
            gqlsq_obj.query = sotagg_query
            gqlsq_obj.variables = {"device_id": ""}
            gqlsq_obj.save()

            gc_setting_obj.sot_agg_query = gqlsq_obj
            gc_setting_obj.save()


class Migration(migrations.Migration):

    dependencies = [
        ("extras", "0018_joblog_data_migration"),
        ("nautobot_golden_config", "0009_multiple_gc_settings"),
    ]

    operations = [
        migrations.AddField(
            model_name="goldenconfigsetting",
            name="sot_agg_query_tmp",
            field=models.TextField(blank=True),
        ),
        migrations.RunPython(save_existing_sotagg_queries),
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
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="sot_aggregation",
                to="extras.graphqlquery",
            ),
        ),
        migrations.RunPython(create_and_link_gql_queries),
        migrations.RemoveField(
            model_name="goldenconfigsetting",
            name="sot_agg_query_tmp",
        ),
    ]
