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
    """Return a list of model instances from a queryset."""
    return (
        format_html("\n".join([core_helpers.hyperlinked_object(instance) for instance in m2m_object.all()]))
        if m2m_object
        else None
    )
