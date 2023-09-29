"""Helper for JSON rendering that extends what Nautobot Core provides."""
import json

from django import template
from django_jinja import library

register = template.Library()


@library.filter()
@register.filter()
def condition_render_json(value):
    """Render a dictionary as formatted JSON conditionally."""
    if isinstance(value, (dict, list)):
        return json.dumps(value, indent=4, sort_keys=True, ensure_ascii=False)
    return value
