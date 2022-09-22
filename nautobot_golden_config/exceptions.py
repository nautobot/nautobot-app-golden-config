"""Nautobot Golden Config Exceptions."""


class MissingReference(Exception):
    """Custom error to signal a missing FK reference when looking up."""


class RenderConfigToPushError(Exception):
    """Exception related to Render Configuration to Push operations."""
