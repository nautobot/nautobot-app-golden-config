"""Custom filter to extend base API for filterform use case."""
import django_filters
from nautobot.apps.filters import FilterExtension


def config_plan_null_search(queryset, name, value):  # pylint: disable=unused-argument
    """Query to ensure config plans are not empty."""
    return queryset.filter(config_plan__isnull=False).distinct()


class JobResultFilterExtension(FilterExtension):
    """Filter provided to be used in select2 query for only jobs that were used by ConfigPlan."""

    model = "extras.jobresult"

    filterset_fields = {
        "nautobot_golden_config_config_plan_null": django_filters.BooleanFilter(
            label="Is FK to ConfigPlan Model", method=config_plan_null_search
        )
    }


filter_extensions = [JobResultFilterExtension]
