"""Nornir job for generating the compliance data."""
# pylint: disable=relative-beyond-top-level
import difflib
import logging
import os

from datetime import datetime

from nornir import InitNornir
from nornir.core.plugins.inventory import InventoryPluginRegister
from nornir.core.task import Result, Task

from nornir_nautobot.plugins.tasks.dispatcher import dispatcher
from nornir_nautobot.plugins.tasks.dispatcher.utils.compliance import parser_map
from nornir_nautobot.utils.logger import NornirLogger
from nornir_nautobot.exceptions import NornirNautobotException

from nautobot_plugin_nornir.plugins.inventory.nautobot_orm import NautobotORMInventory
from nautobot_plugin_nornir.constants import NORNIR_SETTINGS

from nautobot_golden_config.models import ComplianceFeature, ConfigCompliance, GoldenConfigSettings, GoldenConfiguration
from nautobot_golden_config.utilities.helper import (
    get_allowed_os,
    null_to_empty,
    verify_global_settings,
    check_jinja_template,
)
from .processor import ProcessGoldenConfig


InventoryPluginRegister.register("nautobot-inventory", NautobotORMInventory)
LOGGER = logging.getLogger(__name__)


def get_features():
    """A serializer of sorts to return feature mappings as a dictionary."""
    # TODO: Review if creating a proper serializer is the way to go.
    features = {}
    for obj in ComplianceFeature.objects.all():
        platform = str(obj.platform.slug)
        if not features.get(platform):
            features[platform] = []
        features[platform].append(
            {"ordered": obj.config_ordered, "name": obj.name, "section": obj.match_config.splitlines()}
        )
    return features


def diff_files(backup_file, intended_file):
    """Utility function to provide `Unix Diff` between two files."""
    bkup = open(backup_file).readlines()
    intended = open(intended_file).readlines()

    for line in difflib.unified_diff(bkup, intended, lineterm=""):
        yield line


def run_compliance(  # pylint: disable=too-many-arguments,too-many-locals
    task: Task,
    logger,
    global_settings,
    backup_root_path,
    intended_root_folder,
    features,
) -> Result:
    """Prepare data for compliance task.

    Args:
        task (Task): Nornir task individual object

    Returns:
        result (Result): Result from Nornir task
    """
    obj = task.host.data["obj"]

    compliance_obj = GoldenConfiguration.objects.filter(device=obj).first()
    if not compliance_obj:
        compliance_obj = GoldenConfiguration.objects.create(device=obj)
    compliance_obj.compliance_last_attempt_date = task.host.defaults.data["now"]
    compliance_obj.save()

    intended_path_template_obj = check_jinja_template(obj, logger, global_settings.intended_path_template)

    intended_file = os.path.join(intended_root_folder, intended_path_template_obj)

    backup_template = check_jinja_template(obj, logger, global_settings.backup_path_template)
    backup_file = os.path.join(backup_root_path, backup_template)

    platform = obj.platform.slug
    if not features.get(platform):
        logger.log_failure(obj, f"There is no `user` defined feature mapping for platform slug {platform}.")
        raise NornirNautobotException()

    if platform not in parser_map.keys():
        logger.log_failure(obj, f"There is currently no parser support for platform slug {platform}.")
        raise NornirNautobotException()

    feature_data = task.run(
        task=dispatcher,
        name="GET COMPLIANCE FOR CONFIG",
        method="compliance_config",
        obj=obj,
        logger=logger,
        backup_file=backup_file,
        intended_file=intended_file,
        features=features[platform],
        platform=platform,
    )[1].result["feature_data"]

    for feature, value in feature_data.items():
        defaults = {
            "actual": null_to_empty(value["actual"]),
            "intended": null_to_empty(value["intended"]),
            "missing": null_to_empty(value["missing"]),
            "extra": null_to_empty(value["extra"]),
            "compliance": value["compliant"],
            "ordered": value["ordered_compliant"],
        }
        # using update_or_create() method to conveniently update actual obj or create new one.
        ConfigCompliance.objects.update_or_create(
            device=obj,
            feature=feature,
            defaults=defaults,
        )

    compliance_obj.compliance_last_success_date = task.host.defaults.data["now"]
    compliance_obj.compliance_config = "\n".join(diff_files(backup_file, intended_file))
    compliance_obj.save()
    logger.log_success(obj, "Successfully tested complinace.")

    return Result(host=task.host, result=feature_data)


def config_compliance(job_result, data, backup_root_path, intended_root_folder):
    """Nornir play to generate configurations."""
    now = datetime.now()
    features = get_features()
    logger = NornirLogger(__name__, job_result, data.get("debug"))
    global_settings = GoldenConfigSettings.objects.get(id="aaaaaaaa-0000-0000-0000-000000000001")
    verify_global_settings(logger, global_settings, ["backup_path_template", "intended_path_template"])
    nornir_obj = InitNornir(
        runner=NORNIR_SETTINGS.get("runner"),
        logging={"enabled": False},
        inventory={
            "plugin": "nautobot-inventory",
            "options": {
                "credentials_class": NORNIR_SETTINGS.get("credentials"),
                "params": NORNIR_SETTINGS.get("inventory_params"),
                "queryset": get_allowed_os(data),
                "defaults": {"now": now},
            },
        },
    )

    nr_with_processors = nornir_obj.with_processors([ProcessGoldenConfig(logger)])
    nr_with_processors.run(
        task=run_compliance,
        name="RENDER COMPLIANCE TASK GROUP",
        logger=logger,
        global_settings=global_settings,
        backup_root_path=backup_root_path,
        intended_root_folder=intended_root_folder,
        features=features,
    )

    logger.log_debug("Completed Compliance for devices.")
