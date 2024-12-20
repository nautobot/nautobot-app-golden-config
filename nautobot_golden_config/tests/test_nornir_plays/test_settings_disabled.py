"""Unit tests for nautobot_golden_config disabled settings."""

import unittest
from unittest.mock import Mock, patch

from nautobot_golden_config.nornir_plays.config_backup import run_backup
from nautobot_golden_config.nornir_plays.config_compliance import run_compliance
from nautobot_golden_config.nornir_plays.config_deployment import run_deployment
from nautobot_golden_config.nornir_plays.config_intended import run_template


class TestGoldenConfigDisabledSettings(unittest.TestCase):
    """Unit tests for testing disabled settings."""

    def setUp(self):
        # Create a mock object representing the device
        self.obj = Mock()
        self.obj.id = "0000-0000-0000-0000-0000"

        # Create a mock host with necessary attributes
        self.host = Mock()
        self.host.name = "example.rtr"
        self.host.data = {"obj": self.obj}
        self.host.defaults = Mock()
        self.host.defaults.data = {"now": "2024-12-20T12:00:00Z"}

        # Create a mock task with the mock host
        self.task = Mock()
        self.task.host = self.host

        # Create mock settings with compliance disabled
        self.gc_settings = Mock()
        self.gc_settings.compliance_enabled = False
        self.gc_settings.backup_enabled = False
        self.gc_settings.intended_enabled = False
        self.gc_settings.deploy_enabled = False

        # Map device ID to settings
        self.device_to_settings_map = {self.obj.id: self.gc_settings}

        # Create a mock logger
        self.logger = Mock()

        # Define empty rules as compliance is disabled
        self.rules = {}
        self.remove_regex_dict = {}
        self.replace_regex_dict = {}
        self.job_class_instance = Mock()
        self.jinja_env = Mock()
        self.config_plan_qs = Mock()
        self.deploy_job_result = Mock()

    @patch(
        "nautobot_golden_config.utilities.db_management.close_threaded_db_connections",
        lambda x: x,  # No-op decorator
    )
    @patch("nautobot_golden_config.nornir_plays.config_compliance.GoldenConfig")
    @patch("nautobot_golden_config.nornir_plays.config_compliance.render_jinja_template")
    @patch("nautobot_golden_config.nornir_plays.config_compliance.get_rules")
    @patch("nautobot_golden_config.nornir_plays.config_compliance.os.path.exists")
    @patch("nautobot_golden_config.nornir_plays.config_compliance._open_file_config")
    def test_run_compliance_disabled(
        self,
        mock_open_file_config,
        mock_path_exists,
        mock_get_rules,
        mock_render_jinja_template,
        mock_golden_config,
    ):
        """
        Test that run_compliance returns early when compliance is disabled.
        """
        # Execute the function
        run_compliance(self.task, self.logger, self.device_to_settings_map, self.rules)

        # Assertions to verify early exit
        expected_log_message = f"Compliance is disabled for device {self.obj}."
        self.logger.info.assert_called_once_with(expected_log_message)

        # Ensure no further actions are taken
        mock_golden_config.objects.filter.assert_not_called()
        mock_golden_config.objects.create.assert_not_called()
        mock_render_jinja_template.assert_not_called()
        mock_get_rules.assert_not_called()
        mock_path_exists.assert_not_called()
        mock_open_file_config.assert_not_called()

    @patch("nautobot_golden_config.nornir_plays.config_compliance.GoldenConfig")
    @patch("nautobot_golden_config.nornir_plays.config_compliance.render_jinja_template")
    @patch("nautobot_golden_config.nornir_plays.config_compliance.get_rules")
    @patch("nautobot_golden_config.nornir_plays.config_compliance.os.path.exists")
    @patch("nautobot_golden_config.nornir_plays.config_compliance._open_file_config")
    def test_run_backup_disabled(
        self,
        mock_open_file_config,
        mock_path_exists,
        mock_get_rules,
        mock_render_jinja_template,
        mock_golden_config,
    ):
        """
        Test that run_backup returns early when compliance is disabled.
        """
        # Execute the function
        run_backup(self.task, self.logger, self.device_to_settings_map, self.remove_regex_dict, self.replace_regex_dict)

        # Assertions to verify early exit
        expected_log_message = f"Backups are disabled for device {self.obj}."
        self.logger.info.assert_called_once_with(expected_log_message)

        # Ensure no further actions are taken
        mock_golden_config.objects.filter.assert_not_called()
        mock_golden_config.objects.create.assert_not_called()
        mock_render_jinja_template.assert_not_called()
        mock_get_rules.assert_not_called()
        mock_path_exists.assert_not_called()
        mock_open_file_config.assert_not_called()

    @patch("nautobot_golden_config.nornir_plays.config_compliance.GoldenConfig")
    @patch("nautobot_golden_config.nornir_plays.config_compliance.render_jinja_template")
    @patch("nautobot_golden_config.nornir_plays.config_compliance.get_rules")
    @patch("nautobot_golden_config.nornir_plays.config_compliance.os.path.exists")
    @patch("nautobot_golden_config.nornir_plays.config_compliance._open_file_config")
    def test_run_template_disabled(
        self,
        mock_open_file_config,
        mock_path_exists,
        mock_get_rules,
        mock_render_jinja_template,
        mock_golden_config,
    ):
        """
        Test that run_template returns early when compliance is disabled.
        """
        # Execute the function
        run_template(self.task, self.logger, self.device_to_settings_map, self.job_class_instance, self.jinja_env)

        # Assertions to verify early exit
        expected_log_message = f"Intended is disabled for device {self.obj}."
        self.logger.info.assert_called_once_with(expected_log_message)

        # Ensure no further actions are taken
        mock_golden_config.objects.filter.assert_not_called()
        mock_golden_config.objects.create.assert_not_called()
        mock_render_jinja_template.assert_not_called()
        mock_get_rules.assert_not_called()
        mock_path_exists.assert_not_called()
        mock_open_file_config.assert_not_called()

    @patch("nautobot_golden_config.nornir_plays.config_compliance.GoldenConfig")
    @patch("nautobot_golden_config.nornir_plays.config_compliance.render_jinja_template")
    @patch("nautobot_golden_config.nornir_plays.config_compliance.get_rules")
    @patch("nautobot_golden_config.nornir_plays.config_compliance.os.path.exists")
    @patch("nautobot_golden_config.nornir_plays.config_compliance._open_file_config")
    def test_run_deployment_disabled(
        self,
        mock_open_file_config,
        mock_path_exists,
        mock_get_rules,
        mock_render_jinja_template,
        mock_golden_config,
    ):
        """
        Test that run_deployment returns early when compliance is disabled.
        """
        # Execute the function
        run_deployment(self.task, self.logger, self.device_to_settings_map, self.config_plan_qs, self.deploy_job_result)

        # Assertions to verify early exit
        expected_log_message = f"Deploys are disabled for device {self.obj}."
        self.logger.info.assert_called_once_with(expected_log_message)

        # Ensure no further actions are taken
        mock_golden_config.objects.filter.assert_not_called()
        mock_golden_config.objects.create.assert_not_called()
        mock_render_jinja_template.assert_not_called()
        mock_get_rules.assert_not_called()
        mock_path_exists.assert_not_called()
        mock_open_file_config.assert_not_called()
