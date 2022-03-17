from datetime import date
import logging

from django.core.validators import ValidationError
from django.db import migrations

logger = logging.getLogger(__name__)


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
            try:
                gqlsq_obj.clean()
                gqlsq_obj.save()
            except ValidationError:
                msg = f"Could not migrate SoTAgg query for Golden Config Setting {gc_setting_obj.name}"
                logger.warning(msg)
                continue

            gc_setting_obj.sot_agg_query = gqlsq_obj
            try:
                gc_setting_obj.clean()
                gc_setting_obj.save()
            except ValidationError:
                msg = f"Could not save migrated Golden Config Setting {gc_setting_obj.name}"
                logger.warning(msg)
                continue


class Migration(migrations.Migration):

    dependencies = [
        ("nautobot_golden_config", "0016_convert_sotagg_queries_part3"),
    ]

    operations = [
        migrations.RunPython(create_and_link_gql_queries),
    ]
