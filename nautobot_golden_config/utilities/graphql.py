"""Example code to execute GraphQL query from the ORM."""

import logging

from django.utils.module_loading import import_string
from graphene_django.settings import graphene_settings
from graphql import execute, parse
from graphql.error import GraphQLSyntaxError

from nautobot_golden_config.utilities.constant import PLUGIN_CFG

LOGGER = logging.getLogger(__name__)


def graph_ql_query(request, device, query):
    """Function to run graphql and transposer command."""
    LOGGER.debug("GraphQL - request for `%s`", str(device))
    schema = graphene_settings.SCHEMA.graphql_schema

    LOGGER.debug("GraphQL - set query variable to device.")
    variables = {"device_id": str(device.pk)}

    try:
        LOGGER.debug("GraphQL - test query: `%s`", str(query))
        document = parse(query)

    except GraphQLSyntaxError as error:
        LOGGER.warning("GraphQL - test query Failed: `%s`", str(query))
        return (400, {"error": str(error)})

    LOGGER.debug("GraphQL - execute query with variables")
    result = execute(schema=schema, document=document, context_value=request, variable_values=variables)
    if result.errors:
        LOGGER.warning("GraphQL - query executed unsuccessfully")
        for err in result.errors:
            LOGGER.warning("GraphQL - error: `%s`", str(err))
        return (400, result.to_dict())
    data = result.data

    data = data.get("device", {})

    if PLUGIN_CFG.get("sot_agg_transposer"):
        LOGGER.debug("GraphQL - transform data with function: `%s`", str(PLUGIN_CFG.get("sot_agg_transposer")))
        try:
            data = import_string(PLUGIN_CFG.get("sot_agg_transposer"))(data)
        except Exception as error:  # pylint: disable=broad-except
            return (400, {"error": str(error)})

    LOGGER.debug("GraphQL - request successful")
    return (200, data)
