"""Helper functions."""
# pylint: disable=raise-missing-from

from jinja2 import exceptions as jinja_errors

from django import forms
from django.conf import settings

from nautobot.dcim.models import Device
from nautobot.dcim.filters import DeviceFilterSet
from nautobot.utilities.utils import render_jinja2

from nornir_nautobot.exceptions import NornirNautobotException
from nornir_nautobot.utils.logger import NornirLogger

from nautobot_golden_config import models

FIELDS = {
    "platform",
    "tenant_group",
    "tenant",
    "region",
    "site",
    "role",
    "rack",
    "rack_group",
    "manufacturer",
    "device_type",
}


def get_job_filter(data=None):
    """Helper function to return a the filterable list of OS's based on platform.slug and a specific custom value."""
    if not data:
        data = {}
    query = {}
    for field in FIELDS:
        if data.get(field):
            query[f"{field}_id"] = data[field].values_list("pk", flat=True)
    # Handle case where object is from single device run all.
    if data.get("device") and isinstance(data["device"], Device):
        query.update({"id": [str(data["device"].pk)]})
    elif data.get("device"):
        query.update({"id": data["device"].values_list("pk", flat=True)})

    base_qs = models.GoldenConfigSetting.objects.first().get_queryset()
    if DeviceFilterSet(data=query, queryset=base_qs).qs.filter(platform__isnull=True).count() > 0:
        raise NornirNautobotException(
            f"The following device(s) {', '.join([device.name for device in DeviceFilterSet(data=query, queryset=base_qs).qs.filter(platform__isnull=True)])} have no platform defined. Platform is required."
        )

    return DeviceFilterSet(data=query, queryset=base_qs).qs


def null_to_empty(val):
    """Convert to empty string if the value is currently null."""
    if not val:
        return ""
    return val


def verify_global_settings(logger, global_settings, attrs):
    """Helper function to verify required attributes are set before a Nornir play start."""
    for item in attrs:
        if not getattr(global_settings, item):
            logger.log_failure(None, f"Missing the required global setting: `{item}`.")
            raise NornirNautobotException()


def render_jinja_template(obj, logger, template):
    """
    Helper function to render Jinja templates.

    Args:
        obj (Device): The Device object from Nautobot.
        logger (NornirLogger): Logger to log error messages to.
        template (str): A Jinja2 template to be rendered.

    Returns:
        str: The ``template`` rendered.

    Raises:
        NornirNautobotException: When there is an error rendering the ``template``.
    """
    try:
        return render_jinja2(template_code=template, context={"obj": obj})
    except jinja_errors.UndefinedError as error:
        error_msg = (
            "Jinja encountered and UndefinedError`, check the template for missing variable definitions.\n"
            f"Template:\n{template}"
        )
        logger.log_failure(obj, error_msg)
        raise NornirNautobotException from error
    except jinja_errors.TemplateSyntaxError as error:  # Also catches subclass of TemplateAssertionError
        error_msg = (
            f"Jinja encountered a SyntaxError at line number {error.lineno},"
            f"check the template for invalid Jinja syntax.\nTemplate:\n{template}"
        )
        logger.log_failure(obj, error_msg)
        raise NornirNautobotException from error
    # Intentionally not catching TemplateNotFound errors since template is passes as a string and not a filename
    except jinja_errors.TemplateError as error:  # Catches all remaining Jinja errors
        error_msg = (
            "Jinja encountered an unexpected TemplateError; check the template for correctness\n"
            f"Template:\n{template}"
        )
        logger.log_failure(error_msg)
        raise NornirNautobotException from error


def clean_config_settings(repo_type: str, repo_count: int, match_rule: str):
    """Custom clean for `GoldenConfigSettingFeatureForm`.

    Args:
        repo_type (str): `intended` or `backup`.
        repo_count (int): Total number of repos.
        match_rule (str): Template str provided by user to match repos.

    Raises:
        ValidationError: Custom Validation on form.
    """
    if repo_count > 1:
        if not match_rule:
            raise forms.ValidationError(
                f"If you specify more than one {repo_type} repository, you must provide a {repo_type} repository matching rule template."
            )
    elif repo_count == 1 and match_rule:
        raise forms.ValidationError(
            f"If you configure only one {repo_type} repository, there is no need to specify the {repo_type} repository matching rule template."
        )


def get_repository_working_dir(
    repo_type: str,
    obj: Device,
    logger: NornirLogger,
    global_settings: models.GoldenConfigSetting,
) -> str:
    """Match the Device to a repository working directory, based on the repository matching rule.

    Assume that the working directory == the slug of the repo.

    Args:
        repo_type (str): Either `intended` or `backup` repository
        obj (Device): Django ORM Device object.
        logger (NornirLogger): Logger object
        global_settings (models.GoldenConfigSetting): Golden Config global settings.

    Returns:
        str: The local filesystem working directory corresponding to the repo slug.
    """
    match_rule = getattr(global_settings, f"{repo_type}_match_rule")

    if not match_rule and repo_type == "backup":
        return global_settings.backup_repository.first().filesystem_path
    elif not match_rule and repo_type == "intended":
        return global_settings.intended_repository.first().filesystem_path

    desired_repository_slug = render_jinja_template(obj, logger, match_rule)
    matching_repo = getattr(global_settings, f"{repo_type}_repository").filter(slug=desired_repository_slug)
    if len(matching_repo) == 1:
        return f"{settings.GIT_ROOT}/{matching_repo[0].slug}"
    else:
        logger.log_failure(
            obj,
            f"There is no repository slug matching '{desired_repository_slug}' for device. Verify the matching rule and configured Git repositories.",
        )
    return None
