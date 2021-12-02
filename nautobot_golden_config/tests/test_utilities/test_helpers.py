"""Unit tests for nautobot_golden_config utilities helpers."""

import unittest
from unittest.mock import patch

from nautobot.dcim.models import Device

from nornir_nautobot.exceptions import NornirNautobotException
from jinja2 import exceptions as jinja_errors
from nautobot_golden_config.utilities.helper import (
    null_to_empty,
    render_jinja_template,
)


# pylint: disable=no-self-use


class HelpersTest(unittest.TestCase):
    """Test Helper Functions."""

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
