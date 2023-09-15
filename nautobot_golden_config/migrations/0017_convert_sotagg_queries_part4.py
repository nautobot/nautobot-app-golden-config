import logging
from datetime import date

from django.db import migrations

logger = logging.getLogger("nautobot")


def create_and_link_gql_queries(apps, schema_editor):
    """
    Create Saved GraphQL Query objects and link them to SoTAgg Query field.
    """
    GoldenConfigSetting = apps.get_model("nautobot_golden_config", "GoldenConfigSetting")
    GraphQLQuery = apps.get_model("extras", "GraphQLQuery")

    today = str(date.today())

    for gc_setting_obj in GoldenConfigSetting.objects.all():
        if gc_setting_obj.sot_agg_query_tmp:
            gcsetting_name = gc_setting_obj.name
            sotagg_query = gc_setting_obj.sot_agg_query_tmp
            if not sotagg_query.strip().startswith("query ($device_id: ID!)"):
                msg = f"Could not migrate SoTAgg query for Golden Config Setting '{gcsetting_name}'"
                logger.warning(msg)
                continue

            gqlsq_name = f"GC {gcsetting_name} - {today}"
            gqlsq_obj = GraphQLQuery()
            gqlsq_obj.name = gqlsq_name
            gqlsq_obj.query = sotagg_query
            gqlsq_obj.variables = {"device_id": ""}
            gqlsq_obj.save()

            gc_setting_obj.sot_agg_query = gqlsq_obj
            gc_setting_obj.save()
            msg = f"Migrated SoTAgg query for Golden Config Setting '{gcsetting_name}'"
            logger.info(msg)


class Migration(migrations.Migration):
    dependencies = [
        ("nautobot_golden_config", "0016_convert_sotagg_queries_part3"),
    ]

    operations = [
        migrations.RunPython(create_and_link_gql_queries),
    ]
