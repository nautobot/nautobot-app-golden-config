"""Nautobot Golden Config Exceptions."""


class GoldenConfigError(Exception):
    """Parent Exception class for all the Golden Config custom errors."""


class MissingReference(GoldenConfigError):
    """Custom error to signal a missing FK reference when looking up."""


class RenderConfigToPushError(GoldenConfigError):
    """Exception related to Render Configuration Postprocessing operations."""
