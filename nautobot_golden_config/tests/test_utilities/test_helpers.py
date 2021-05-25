"""Unit tests for nautobot_golden_config utilities helpers."""

import unittest
from unittest.mock import patch, Mock
from nornir_nautobot.exceptions import NornirNautobotException
from jinja2.exceptions import TemplateError
from nautobot_golden_config.utilities.helper import (
    null_to_empty,
    check_jinja_template,
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

    def test_check_jinja_template_success(self):
        """Simple success test to return template."""
        worker = check_jinja_template("obj", "logger", "fake-template-name")
        self.assertEqual(worker, "fake-template-name")

    def test_check_jinja_template_exceptions_undefined(self):
        """Use fake obj key to cause UndefinedError from Jinja2 Template."""
        log_mock = Mock()
        with self.assertRaises(NornirNautobotException):
            check_jinja_template("test-obj", log_mock, "{{ obj.fake }}")

    def test_check_jinja_template_exceptions_syntaxerror(self):
        """Use invalid templating to cause TemplateSyntaxError from Jinja2 Template."""
        log_mock = Mock()
        with self.assertRaises(NornirNautobotException):
            check_jinja_template("test-obj", log_mock, "{{ obj.fake }")

    @patch("nautobot_golden_config.utilities.helper.Template")
    def test_check_jinja_template_exceptions_templateerror(self, template_mock):
        """Cause issue to cause TemplateError form Jinja2 Template."""
        log_mock = Mock()
        with self.assertRaises(NornirNautobotException):
            template_mock.side_effect = TemplateError
            template_render = check_jinja_template("test-obj", log_mock, "template")
            self.assertEqual(template_render, TemplateError)
            template_mock.assert_called_once()
