"""Renderer classes for special use cases, such as plain text rendering."""
from rest_framework import renderers

from django.utils.encoding import smart_text


class PlainTextRenderer(renderers.BaseRenderer):
    """Renderer for plain text."""

    media_type = "text/plain"
    format = "txt"

    def render(self, data, accepted_media_type=None, renderer_context=None):
        """Render text.

        Args:
            data (str): Data to be rendered in plain text format.
            accepted_media_type (text, optional): Standard media type <MIME_type>/<MIME_subtype>. Defaults to None.
            renderer_context (str, optional): _description_. Defaults to None.

        Returns:
            str: Text with proper encoding.
        """
        return smart_text(data, encoding=self.charset)
