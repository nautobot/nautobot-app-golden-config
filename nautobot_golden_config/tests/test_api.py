"""Unit tests for nautobot_golden_config."""
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils.module_loading import import_string

from django.urls import reverse
from rest_framework import status

from nautobot.utilities.testing import APITestCase
from nautobot_golden_config.choices import ComplianceRuleTypeChoice

from .conftest import create_device, create_feature_rule_json, create_config_compliance, create_feature_rule_custom


User = get_user_model()


class GoldenConfigJSONAPITest(APITestCase):  # pylint: disable=too-many-ancestors
    """Test the ConfigCompliance API."""

    def setUp(self):
        """Create a superuser and token for API calls."""
        super().setUp()
        self.device = create_device()
        self.compliance_rule_json = create_feature_rule_json(self.device)
        self.base_view = reverse("plugins-api:nautobot_golden_config-api:configcompliance-list")

    def test_root(self):
        """Validate the root for Nautobot API."""
        url = reverse("plugins-api:nautobot_golden_config-api:api-root")
        response = self.client.get(f"{url}?format=api", **self.header)
        self.assertEqual(response.status_code, 200)

    def test_device_list(self):
        """Verify that devices can be listed."""
        url = reverse("dcim-api:device-list")
        self.add_permissions("dcim.view_device")
        response = self.client.get(url, **self.header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    def test_config_compliance_list_view(self):
        """Verify that config compliance objects can be listed."""
        actual = '{"foo": {"bar-1": "baz"}}'
        intended = '{"foo": {"bar-2": "baz"}}'
        create_config_compliance(
            self.device, actual=actual, intended=intended, compliance_rule=self.compliance_rule_json
        )
        self.add_permissions("nautobot_golden_config.view_configcompliance")
        response = self.client.get(self.base_view, **self.header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    def test_config_compliance_post_new_json_compliant(self):
        """Verify that config compliance detail view."""
        self.add_permissions("nautobot_golden_config.add_configcompliance")
        response = self.client.post(
            self.base_view,
            data={
                "device": self.device.id,
                "intended": '{"foo": {"bar-1": "baz"}}',
                "actual": '{"foo": {"bar-1": "baz"}}',
                "rule": self.compliance_rule_json.id,
            },
            format="json",
            **self.header,
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["compliance"])

    def test_config_compliance_post_new_json_not_compliant(self):
        """Verify that config compliance detail view."""
        self.add_permissions("nautobot_golden_config.add_configcompliance")
        response = self.client.post(
            self.base_view,
            data={
                "device": self.device.id,
                "intended": '{"foo": {"bar-1": "baz"}}',
                "actual": '{"foo": {"bar-2": "baz"}}',
                "rule": self.compliance_rule_json.id,
            },
            format="json",
            **self.header,
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertFalse(response.data["compliance"])


class GoldenConfigCustomAPITest(APITestCase):  # pylint: disable=too-many-ancestors
    """Test the ConfigCompliance API."""

    def setUp(self):
        """Create a superuser and token for API calls."""
        super().setUp()
        self.device = create_device()
        self.compliance_rule_custom = create_feature_rule_custom(self.device)
        self.base_view = reverse("plugins-api:nautobot_golden_config-api:configcompliance-list")

    def test_root(self):
        """Validate the root for Nautobot Golden Config API."""
        url = reverse("plugins-api:nautobot_golden_config-api:api-root")
        response = self.client.get(f"{url}?format=api", **self.header)
        self.assertEqual(response.status_code, 200)

    def test_device_list(self):
        """Verify that devices can be listed."""
        url = reverse("dcim-api:device-list")
        self.add_permissions("dcim.view_device")
        response = self.client.get(url, **self.header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    @patch.dict(
        "nautobot_golden_config.models.FUNC_MAPPER",
        {ComplianceRuleTypeChoice.TYPE_CUSTOM: import_string("nautobot_golden_config.tests.custom_compliance_func")},
    )
    def test_config_compliance_list_view(self):
        """Verify that config compliance objects can be listed."""
        actual = '{"foo": {"bar-1": "baz"}}'
        intended = '{"foo": {"bar-2": "baz"}}'
        create_config_compliance(
            self.device, actual=actual, intended=intended, compliance_rule=self.compliance_rule_custom
        )
        self.add_permissions("nautobot_golden_config.view_configcompliance")
        response = self.client.get(self.base_view, **self.header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    @patch.dict(
        "nautobot_golden_config.models.FUNC_MAPPER",
        {ComplianceRuleTypeChoice.TYPE_CUSTOM: import_string("nautobot_golden_config.tests.custom_compliance_func")},
    )
    def test_config_compliance_post_new_custom_compliant(self):
        """Verify that config compliance detail view for custom compliance."""
        self.add_permissions("nautobot_golden_config.add_configcompliance")
        response = self.client.post(
            self.base_view,
            data={
                "device": self.device.id,
                "intended": '{"foo": "bar-2\n bar\n password bar"}',
                "actual": '{"foo": "bar-1\n bar\n password bar"}',
                "rule": self.compliance_rule_custom.id,
            },
            format="json",
            **self.header,
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["compliance"])

    @patch.dict(
        "nautobot_golden_config.models.FUNC_MAPPER",
        {ComplianceRuleTypeChoice.TYPE_CUSTOM: import_string("nautobot_golden_config.tests.custom_compliance_func")},
    )
    def test_config_compliance_post_new_custom_not_compliant(self):
        """Verify that config compliance detail view for custom compliance."""
        self.add_permissions("nautobot_golden_config.add_configcompliance")
        response = self.client.post(
            self.base_view,
            data={
                "device": self.device.id,
                "intended": '{"foo": "bar-2\n bar\n password bar"}',
                "actual": '{"foo": "bar-1\n bar\n bar"}',
                "rule": self.compliance_rule_custom.id,
            },
            format="json",
            **self.header,
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertFalse(response.data["compliance"])

    def test_config_compliance_post_new_custom_no_func(self):
        """Verify that custom config compliance raises an Exception when no custom function can be imported."""
        with self.assertRaises(ValidationError):
            actual = '{"foo": {"bar-1": "baz"}}'
            intended = '{"foo": {"bar-2": "baz"}}'
            create_config_compliance(
                self.device, actual=actual, intended=intended, compliance_rule=self.compliance_rule_custom
            )
