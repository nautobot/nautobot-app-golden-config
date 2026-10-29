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


class ConfigPlanDeploymentFailure(GoldenConfigError):
    """Custom error for when there's a failure in Config Plan Deployment Job."""


class PartialMatchConfigError(GoldenConfigError):
    """Custom error for an invalid match_config on a Partial CLI compliance rule."""
