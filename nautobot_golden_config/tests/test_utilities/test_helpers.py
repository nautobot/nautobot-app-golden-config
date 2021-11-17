"""Unit tests for nautobot_golden_config utilities helpers."""

import unittest
from unittest.mock import patch, Mock

from nautobot.dcim.models import Device

from nornir_nautobot.exceptions import NornirNautobotException
from jinja2.exceptions import TemplateError
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
        platform = "mock_platform"
        mock_device.platform = platform
        rendered_template = render_jinja_template(mock_device, "logger", "{{ obj.platform }}")
        self.assertEqual(rendered_template, platform)

    @patch("nautobot.dcim.models.Device")
    def test_render_jinja_template_success_with_filter(self, mock_device):
        """Test custom template is accessible."""
        rendered_template = render_jinja_template(mock_device, "logger", "{{ data | return_a }}")
        self.assertEqual(rendered_template, "a")

    @unittest.skip("Need to figure out why this does not raise an exception")
    @patch("nautobot.dcim.models.Device", spec=Device)
    def test_render_jinja_template_exceptions_undefined(self, mock_device):
        """Use fake obj key to cause UndefinedError from Jinja2 Template."""
        log_mock = Mock()
        with self.assertRaises(NornirNautobotException):
            render_jinja_template(mock_device, log_mock, "{{ obj.fake }}")

    @patch("nautobot.dcim.models.Device")
    def test_render_jinja_template_exceptions_syntaxerror(self, mock_device):
        """Use invalid templating to cause TemplateSyntaxError from Jinja2 Template."""
        log_mock = Mock()
        with self.assertRaises(NornirNautobotException):
            render_jinja_template(mock_device, log_mock, "{{ obj.fake }")

    @patch("nautobot.dcim.models.Device")
    @patch("nautobot_golden_config.utilities.helper.render_jinja2")
    def test_render_jinja_template_exceptions_templateerror(self, template_mock, mock_device):
        """Cause issue to cause TemplateError form Jinja2 Template."""
        log_mock = Mock()
        with self.assertRaises(NornirNautobotException):
            template_mock.side_effect = TemplateError
            template_render = render_jinja_template(mock_device, log_mock, "template")
            self.assertEqual(template_render, TemplateError)
            template_mock.assert_called_once()
