"""Helpers for UI component rendering that extends what Nautobot Core provides."""

from django import template
from django.urls import reverse
from django.utils.html import format_html
from django_jinja import library

register = template.Library()


@library.filter()
@register.filter()
def hyperlinked_field_with_icon(device_pk, title, gc_view, icon_class="mdi mdi-text-box-check-outline"):
    """Render a redirect link with custom icon."""
    url = reverse(viewname=f"plugins:nautobot_golden_config:goldenconfig_{gc_view}", kwargs={"pk": device_pk})
    return format_html('<a href="{}"><i class="{}" title="{}"></i></a>', url, icon_class, title)
