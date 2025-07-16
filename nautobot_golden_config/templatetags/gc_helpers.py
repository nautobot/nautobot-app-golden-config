"""Helpers for UI component rendering that extends what Nautobot Core provides."""

from django import template
from django.utils.html import format_html
from django_jinja import library
from nautobot.core.templatetags import helpers as core_helpers

register = template.Library()


@library.filter()
@register.filter()
def hyperlinked_field_with_icon(url, title, icon_class="mdi mdi-text-box-check-outline"):
    """Render a redirect link with custom icon."""
    return format_html('<a href="{}"><i class="{}" title="{}"></i></a>', url, icon_class, title)


@library.filter()
@register.filter()
def get_model_instances(m2m_object):
    """Return a unordered bullet list of model instances from a m2m object."""
    if m2m_object.count() == 0:
        return None
    ul_elements = []
    for obj in m2m_object.all():
        ul_elements.append(f"<li>{core_helpers.hyperlinked_object(obj)}</li>")
    return format_html(f"<ul>{''.join(ul_elements)}</ul>")
