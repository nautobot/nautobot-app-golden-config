"""Nautobot Golden Config Exceptions."""


class GoldenConfigError(Exception):
    """Parent Exception class for all the Golden Config custom errors."""


class MissingReference(GoldenConfigError):
    """Custom error to signal a missing FK reference when looking up."""


class MultipleReferences(GoldenConfigError):
    """Custom error to signal a get() returned more than 1 FK reference when looking up."""


class RenderConfigToPushError(GoldenConfigError):
    """Exception related to Render Configuration Postprocessing operations."""


class BackupFailure(GoldenConfigError):
    """Custom error for when there's a failure in Backup Job."""


class IntendedGenerationFailure(GoldenConfigError):
    """Custom error for when there's a failure in Intended Job."""


class ComplianceFailure(GoldenConfigError):
    """Custom error for when there's a failure in Compliance Job."""
