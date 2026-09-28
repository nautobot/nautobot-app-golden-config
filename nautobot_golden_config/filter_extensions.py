"""FilterSet and FilterForm extensions for the Golden Config app."""

from django.db.models import Q
from nautobot.apps.filters import FilterExtension, MultiValueCharFilter


def filter_graphql_query_variables(queryset, name, value):  # pylint: disable=unused-argument
    """Filter the queryset based on the presence of variables."""
    query = Q()
    for variable_name in value:
        query |= Q(**{f"variables__{variable_name}__isnull": True})
    return queryset.exclude(query)


class GraphQLQueryFilterExtension(FilterExtension):
    """Filter extensions for the extras.GraphQLQuery model."""

    model = "extras.graphqlquery"

    filterset_fields = {
        "nautobot_golden_config_graphql_query_variables": MultiValueCharFilter(
            field_name="variables",
            lookup_expr="exact",
            method=filter_graphql_query_variables,
            label="Variable key(s) exist",
        ),
    }


filter_extensions = [GraphQLQueryFilterExtension]
