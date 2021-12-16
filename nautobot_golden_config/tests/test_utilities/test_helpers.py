"""Unit tests for nautobot_golden_config utilities helpers."""

from unittest.mock import patch, MagicMock

from django.test import TestCase

from nornir_nautobot.exceptions import NornirNautobotException
from nornir_nautobot.utils.logger import NornirLogger
from jinja2 import exceptions as jinja_errors

from nautobot.dcim.models import Device
from nautobot.extras.models import GitRepository
from nautobot_golden_config.models import GoldenConfigSetting
from nautobot_golden_config.tests.conftest import create_device, create_orphan_device, create_helper_repo
from nautobot_golden_config.utilities.helper import null_to_empty, render_jinja_template, get_repository_working_dir


# pylint: disable=no-self-use


class HelpersTest(TestCase):
    """Test Helper Functions."""

    def setUp(self):
        """Setup a reusable mock object to pass into GitRepo."""
        self.repository_obj = MagicMock()
        self.repository_obj.path = "/fake/path"
        GitRepository.objects.all().delete()
        create_helper_repo(name="backup-parent_region-1", provides="backupconfigs")
        create_helper_repo(name="intended-parent_region-1", provides="intendedconfigs")
        create_helper_repo(name="test-jinja-repo", provides="jinjatemplate")
        self.global_settings = GoldenConfigSetting.objects.first()
        self.global_settings.backup_repository.set([GitRepository.objects.get(name="backup-parent_region-1")])
        self.global_settings.intended_repository.set([GitRepository.objects.get(name="intended-parent_region-1")])
        self.global_settings.jinja_repository = GitRepository.objects.get(name="test-jinja-repo")
        self.global_settings.backup_repository_template = "backup-{{ obj.site.region.parent.slug }}"
        self.global_settings.intended_repository_template = "intended-{{ obj.site.region.parent.slug }}"
        # Device.objects.all().delete()
        create_device(name="test_device")
        create_orphan_device(name="orphan_device")
        self.job_result = MagicMock()
        self.data = MagicMock()
        self.logger = NornirLogger(__name__, self.job_result, self.data)

    def test_null_to_empty_null(self):
        """Ensure None returns with empty string."""
        result = null_to_empty(None)
        self.assertEqual(result, "")

    def test_null_to_empty_val(self):
        """Ensure if not None input is returned."""
        result = null_to_empty("test")
        self.assertEqual(result, "test")

    @patch("nautobot.dcim.models.Device")
    def test_render_jinja_template_success(self, mock_device):
        """Simple success test to return template."""
        worker = render_jinja_template(mock_device, "logger", "fake-template-contents")
        self.assertEqual(worker, "fake-template-contents")

    @patch("nautobot.dcim.models.Device")
    def test_render_jinja_template_success_render_context(self, mock_device):
        """Test that device object is passed to template context."""
        platform = "mock_platform"
        mock_device.platform = platform
        rendered_template = render_jinja_template(mock_device, "logger", "{{ obj.platform }}")
        self.assertEqual(rendered_template, platform)

    @patch("nautobot.dcim.models.Device")
    def test_render_jinja_template_success_with_filter(self, mock_device):
        """Test custom template and jinja filter are accessible."""
        rendered_template = render_jinja_template(mock_device, "logger", "{{ data | return_a }}")
        self.assertEqual(rendered_template, "a")

    @patch("nornir_nautobot.utils.logger.NornirLogger")
    @patch("nautobot.dcim.models.Device", spec=Device)
    def test_render_jinja_template_exceptions_undefined(self, mock_device, mock_nornir_logger):
        """Use fake obj key to cause UndefinedError from Jinja2 Template."""
        with self.assertRaises(NornirNautobotException):
            with self.assertRaises(jinja_errors.UndefinedError):
                render_jinja_template(mock_device, mock_nornir_logger, "{{ obj.fake }}")
        mock_nornir_logger.log_failure.assert_called_once()

    @patch("nornir_nautobot.utils.logger.NornirLogger")
    @patch("nautobot.dcim.models.Device")
    def test_render_jinja_template_exceptions_syntaxerror(self, mock_device, mock_nornir_logger):
        """Use invalid templating to cause TemplateSyntaxError from Jinja2 Template."""
        with self.assertRaises(NornirNautobotException):
            with self.assertRaises(jinja_errors.TemplateSyntaxError):
                render_jinja_template(mock_device, mock_nornir_logger, "{{ obj.fake }")
        mock_nornir_logger.log_failure.assert_called_once()

    @patch("nornir_nautobot.utils.logger.NornirLogger")
    @patch("nautobot.dcim.models.Device")
    @patch("nautobot_golden_config.utilities.helper.render_jinja2")
    def test_render_jinja_template_exceptions_templateerror(self, template_mock, mock_device, mock_nornir_logger):
        """Cause issue to cause TemplateError form Jinja2 Template."""
        with self.assertRaises(NornirNautobotException):
            with self.assertRaises(jinja_errors.TemplateError):
                template_mock.side_effect = jinja_errors.TemplateRuntimeError
                render_jinja_template(mock_device, mock_nornir_logger, "template")
        mock_nornir_logger.log_failure.assert_called_once()

    def test_get_backup_repository_working_dir_success(self):
        """Verify that we successfully look up the path from a provided repo object."""
        repo_type = "backup"
        result = get_repository_working_dir(
            self.repository_obj, repo_type, Device.objects.get(name="test_device"), self.logger, self.global_settings
        )
        self.assertEqual(result, "/opt/nautobot/git/backup-parent_region-1")

    def test_get_intended_repository_working_dir_success(self):
        """Verify that we successfully look up the path from a provided repo object."""
        repo_type = "intended"
        result = get_repository_working_dir(
            self.repository_obj, repo_type, Device.objects.get(name="test_device"), self.logger, self.global_settings
        )
        self.assertEqual(result, "/opt/nautobot/git/intended-parent_region-1")

    def test_get_backup_repository_working_dir_no_match(self):
        """Verify that we return the correct error when there is no matching backup repo."""
        repo_type = "backup"
        logger = MagicMock()
        result = get_repository_working_dir(
            self.repository_obj, repo_type, Device.objects.get(name="orphan_device"), logger, self.global_settings
        )
        self.assertEqual(result, "/fake/path")
        self.assertEqual(logger.log_failure.call_count, 1)
        self.assertEqual(
            logger.log_failure.call_args[0][1],
            "There is no repository slug matching 'backup-parent_region-4' for device. Verify the matching rule and configured Git repositories.",
        )

    def test_get_intended_repository_working_dir_no_match(self):
        """Verify that we return the correct error when there is no matching intended repo."""
        repo_type = "intended"
        logger = MagicMock()
        result = get_repository_working_dir(
            self.repository_obj, repo_type, Device.objects.get(name="orphan_device"), logger, self.global_settings
        )
        self.assertEqual(result, "/fake/path")
        self.assertEqual(logger.log_failure.call_count, 1)
        self.assertEqual(
            logger.log_failure.call_args[0][1],
            "There is no repository slug matching 'intended-parent_region-4' for device. Verify the matching rule and configured Git repositories.",
        )
