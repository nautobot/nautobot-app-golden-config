"""Tests for the move of the app-level `enable_*` settings onto `GoldenConfigSetting`."""

from importlib import import_module
from types import SimpleNamespace

from django.apps import apps
from django.db import connection
from django.test import override_settings
from nautobot.apps.testing import TestCase

from nautobot_golden_config.models import GoldenConfigSetting
from nautobot_golden_config.tests.conftest import dgs_gc_settings_and_job_repo_objects

FLAGS = (
    "enable_backup",
    "enable_compliance",
    "enable_intended",
    "enable_sotagg",
    "enable_plan",
    "enable_deploy",
    "enable_postprocessing",
)

migration = import_module("nautobot_golden_config.migrations.0033_goldenconfigsetting_enable_flags_from_app_config")


class EnableFlagsDataMigrationTestCase(TestCase):
    """The data migration carries the app-level `enable_*` settings onto existing Settings."""

    @classmethod
    def setUpTestData(cls):
        dgs_gc_settings_and_job_repo_objects()

    def _run_migration(self):
        schema_editor = SimpleNamespace(connection=connection)
        migration.copy_enable_flags_from_app_config(apps, schema_editor)

    def test_configured_values_are_copied_onto_every_setting(self):
        app_config = {"enable_backup": False, "enable_deploy": False, "enable_postprocessing": True}
        with override_settings(PLUGINS_CONFIG={"nautobot_golden_config": app_config}):
            self._run_migration()

        self.assertTrue(GoldenConfigSetting.objects.exists())
        for setting in GoldenConfigSetting.objects.all():
            for flag in FLAGS:
                with self.subTest(setting=setting.name, flag=flag):
                    self.assertEqual(getattr(setting, flag), app_config.get(flag, True))

    def test_unset_values_fall_back_to_previous_app_defaults(self):
        GoldenConfigSetting.objects.update(enable_backup=False, enable_postprocessing=True)
        with override_settings(PLUGINS_CONFIG={"nautobot_golden_config": {}}):
            self._run_migration()

        for setting in GoldenConfigSetting.objects.all():
            for flag in FLAGS:
                with self.subTest(setting=setting.name, flag=flag):
                    self.assertEqual(getattr(setting, flag), flag != "enable_postprocessing")


class DeprecatedEnableSettingsWarningTestCase(TestCase):
    """Startup warns while the removed app-level `enable_*` settings are still configured."""

    def setUp(self):
        self.app_config = apps.get_app_config("nautobot_golden_config")

    def test_warning_names_the_configured_settings(self):
        app_config = {"enable_backup": True, "enable_deploy": False, "per_feature_width": 13}
        with override_settings(PLUGINS_CONFIG={"nautobot_golden_config": app_config}):
            with self.assertLogs("nautobot_golden_config", level="WARNING") as logs:
                self.app_config._warn_deprecated_enable_settings()  # pylint: disable=protected-access

        self.assertEqual(len(logs.output), 1)
        self.assertIn("`enable_backup`, `enable_deploy`", logs.output[0])
        self.assertNotIn("per_feature_width", logs.output[0])

    def test_no_warning_without_deprecated_settings(self):
        with override_settings(PLUGINS_CONFIG={"nautobot_golden_config": {"per_feature_width": 13}}):
            with self.assertNoLogs("nautobot_golden_config", level="WARNING"):
                self.app_config._warn_deprecated_enable_settings()  # pylint: disable=protected-access
