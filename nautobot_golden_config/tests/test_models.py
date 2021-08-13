"""Unit tests for nautobot_golden_config models."""

import json
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from nautobot.dcim.models import Platform

from nautobot_golden_config.models import (
    ConfigCompliance,
    GoldenConfigSetting,
    ConfigRemove,
    ConfigReplace,
)

from .conftest import create_device, create_feature_rule_json, create_config_compliance


class ConfigComplianceModelTestCase(TestCase):
    """Test CRUD operations for ConfigCompliance Model."""

    def setUp(self):
        """Set up base objects."""
        self.device = create_device()
        self.compliance_rule_json = create_feature_rule_json(self.device)

    def test_create_config_compliance_success_json(self):
        """Successful."""
        actual = '{"foo": {"bar-1": "baz"}}'
        intended = '{"foo": {"bar-2": "baz"}}'
        cc_obj = create_config_compliance(
            self.device, actual=actual, intended=intended, compliance_rule=self.compliance_rule_json
        )

        self.assertFalse(cc_obj.compliance)
        self.assertEqual(cc_obj.actual, json.dumps({"foo": {"bar-1": "baz"}}))
        self.assertEqual(cc_obj.intended, json.dumps({"foo": {"bar-2": "baz"}}))
        self.assertEqual(cc_obj.missing, ["root['foo']['bar-2']"])
        self.assertEqual(cc_obj.extra, ["root['foo']['bar-1']"])

    def test_create_config_compliance_unique_failure(self):
        """Raises error when attempting to create duplicate."""
        ConfigCompliance.objects.create(
            device=self.device,
            rule=self.compliance_rule_json,
            actual='{"foo": {"bar-1": "baz"}}',
            intended='{"foo": {"bar-2": "baz"}}',
            missing={},
            extra={},
        )
        with self.assertRaises(IntegrityError):
            ConfigCompliance.objects.create(
                device=self.device,
                rule=self.compliance_rule_json,
                compliance=False,
                actual='{"foo": {"bar-1": "baz"}}',
                intended='{"foo": {"bar-2": "baz"}}',
                missing={},
                extra={},
            )

    def test_create_config_compliance_success_compliant(self):
        """Successful."""
        cc_obj = ConfigCompliance.objects.create(
            device=self.device,
            rule=self.compliance_rule_json,
            actual='{"foo": {"bar-1": "baz"}}',
            intended='{"foo": {"bar-1": "baz"}}',
        )

        self.assertTrue(cc_obj.compliance)
        self.assertEqual(cc_obj.missing, "")
        self.assertEqual(cc_obj.extra, "")


class GoldenConfigTestCase(TestCase):
    """Test GoldenConfig Model."""


class ComplianceRuleTestCase(TestCase):
    """Test ComplianceRule Model."""


class GoldenConfigSettingModelTestCase(TestCase):
    """Test GoldenConfigSetting Model."""

    def setUp(self):
        """Get the golden config settings with the only allowed id."""
        self.global_settings = GoldenConfigSetting.objects.first()

    def test_bad_graphql_query(self):
        """Invalid graphql query."""
        self.global_settings.sot_agg_query = 'devices(name:"ams-edge-01")'
        with self.assertRaises(ValidationError):
            self.global_settings.clean()

    def test_good_graphql_query_invalid_starts_with(self):
        """Valid graphql query, however invalid in the usage with golden config plugin."""
        self.global_settings.sot_agg_query = '{devices(name:"ams-edge-01"){id}}'
        with self.assertRaises(ValidationError) as error:
            self.global_settings.clean()
        self.assertEqual(error.exception.message, "The GraphQL query must start with exactly `query ($device_id: ID!)`")

    def test_good_graphql_query_validate_starts_with(self):
        """Ensure clean() method returns None when valid query is sent through."""
        self.global_settings.sot_agg_query = "query ($device_id: ID!) {device(id: $device_id) {id}}"
        self.assertEqual(self.global_settings.clean(), None)


class ConfigRemoveModelTestCase(TestCase):
    """Test ConfigRemove Model."""

    def setUp(self):
        """Setup Object."""
        self.platform = Platform.objects.create(slug="cisco_ios")
        self.line_removal = ConfigRemove.objects.create(
            name="foo", platform=self.platform, description="foo bar", regex="^Back.*"
        )

    def test_add_line_removal_entry(self):
        """Test Add Object."""
        self.assertEqual(self.line_removal.name, "foo")
        self.assertEqual(self.line_removal.description, "foo bar")
        self.assertEqual(self.line_removal.regex, "^Back.*")

    def test_edit_line_removal_entry(self):
        """Test Edit Object."""
        new_name = "Line Remove"
        new_desc = "Testing Remove Running Config Line"
        new_regex = "^Running.*"
        self.line_removal.name = new_name
        self.line_removal.description = new_desc
        self.line_removal.regex = new_regex
        self.line_removal.save()

        self.assertEqual(self.line_removal.name, new_name)
        self.assertEqual(self.line_removal.description, new_desc)
        self.assertEqual(self.line_removal.regex, new_regex)


class ConfigReplaceModelTestCase(TestCase):
    """Test ConfigReplace Model."""

    def setUp(self):
        """Setup Object."""
        self.platform = Platform.objects.create(slug="cisco_ios")
        self.line_replace = ConfigReplace.objects.create(
            name="foo",
            platform=self.platform,
            description="foo bar",
            regex=r"username(\S+)",
            replace="<redacted>",
        )

    def test_add_line_replace_entry(self):
        """Test Add Object."""
        self.assertEqual(self.line_replace.name, "foo")
        self.assertEqual(self.line_replace.description, "foo bar")
        self.assertEqual(self.line_replace.regex, r"username(\S+)")
        self.assertEqual(self.line_replace.replace, "<redacted>")

    def test_edit_line_replace_entry(self):
        """Test Edit Object."""
        new_name = "Line Replacement"
        new_desc = "Testing Replacing Config Line"
        new_regex = r"password(\S+)"
        self.line_replace.name = new_name
        self.line_replace.description = new_desc
        self.line_replace.regex = new_regex
        self.line_replace.save()

        self.assertEqual(self.line_replace.name, new_name)
        self.assertEqual(self.line_replace.description, new_desc)
        self.assertEqual(self.line_replace.regex, new_regex)
        self.assertEqual(self.line_replace.replace, "<redacted>")
