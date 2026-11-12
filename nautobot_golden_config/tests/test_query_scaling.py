"""Tests that resolving Golden Config Settings does not issue queries per device."""

from unittest.mock import MagicMock, patch

from django.db import connection
from django.test.utils import CaptureQueriesContext
from nautobot.apps.testing import TestCase
from nautobot.dcim.models import Device
from nautobot.extras.models import Status

from nautobot_golden_config import jobs
from nautobot_golden_config.models import ConfigPlan
from nautobot_golden_config.tests.conftest import (
    create_device,
    create_job_result,
    create_orphan_device,
    dgs_gc_settings_and_job_repo_objects,
)
from nautobot_golden_config.utilities.helper import (
    filter_devices_by_feature_enabled,
    get_device_to_settings_map,
    update_dynamic_groups_cache,
)


def _query_count(func):
    """Return how many queries `func` issues."""
    with CaptureQueriesContext(connection) as context:
        func()
    return len(context.captured_queries)


def _setup_job(job_class):
    """Run the shared Golden Config job setup for every device, without touching Git."""
    job = job_class()
    with patch("nautobot_golden_config.jobs.ensure_git_repository", MagicMock()):
        job.gc_job_setup(data={"device": Device.objects.all()})


def _filter_deploy_plans():
    list(jobs._filter_config_plans_by_deploy_enabled(MagicMock(), ConfigPlan.objects.all()))  # pylint: disable=protected-access


SETTING_RESOLUTION_PATHS = {
    "get_device_to_settings_map": lambda: get_device_to_settings_map(Device.objects.all()),
    "filter_devices_by_feature_enabled": lambda: list(
        filter_devices_by_feature_enabled(MagicMock(), Device.objects.all(), "plan")
    ),
    "single-feature job setup": lambda: _setup_job(jobs.BackupJob),
    "all-in-one job setup": lambda: _setup_job(jobs.AllDevicesGoldenConfig),
    "deploy plan filter": _filter_deploy_plans,
}


class SettingResolutionQueryScalingTestCase(TestCase):
    """Query counts for Setting resolution stay flat as the number of devices grows."""

    @classmethod
    def setUpTestData(cls):
        create_device(name="scale-a-0")
        create_orphan_device(name="scale-b-0")
        dgs_gc_settings_and_job_repo_objects()

    def _measure(self):
        """Count the queries of each path with one approved ConfigPlan per device."""
        status = Status.objects.get(name="Approved")
        plan_result = create_job_result()
        for device in Device.objects.filter(config_plan__isnull=True):
            ConfigPlan.objects.create(
                device=device, plan_type="manual", config_set="hostname x", status=status, plan_result=plan_result
            )
        # Adding devices to a Dynamic Group's member cache issues writes the first time only.
        update_dynamic_groups_cache()
        return {name: _query_count(path) for name, path in SETTING_RESOLUTION_PATHS.items()}

    def test_query_count_does_not_grow_with_devices(self):
        with_two_devices = self._measure()
        for index in range(1, 10):
            create_device(name=f"scale-a-{index}")
            create_orphan_device(name=f"scale-b-{index}")
        self.assertEqual(Device.objects.count(), 20)
        with_twenty_devices = self._measure()

        for name, small in with_two_devices.items():
            with self.subTest(path=name):
                self.assertEqual(with_twenty_devices[name], small)

    def test_selected_device_missing_from_settings_map_is_logged(self):
        """A device the job form matched but no Setting's cached membership contains gets an E3038."""
        job = jobs.BackupJob()
        job.qs = Device.objects.filter(name="scale-a-0")
        job.device_to_settings = {}

        with self.assertLogs(job.logger, level="WARNING") as logs:
            job._log_unscoped_devices()  # pylint: disable=protected-access

        self.assertEqual(len(logs.output), 1)
        self.assertIn(
            "E3038: Device scale-a-0 skipped for backup job — no eligible Golden Config Setting", logs.output[0]
        )
