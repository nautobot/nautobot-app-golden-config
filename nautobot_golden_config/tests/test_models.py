"""Unit tests for nautobot_golden_config models."""

import unittest
from django.core.exceptions import ValidationError

from nautobot_golden_config.models import GoldenConfigSettings


class GoldenConfigSettingsModelTestCase(unittest.TestCase):
    """Test GoldenConfigSettings Model."""

    def setUp(self):
        """Get the golden config settings with the only allowed id."""
        self.global_settings = GoldenConfigSettings.objects.get(id="aaaaaaaa-0000-0000-0000-000000000001")

    def test_only_valid_id(self):
        """Get global settings and ensure we received the allowed id."""
        self.assertEqual(str(self.global_settings.pk), "aaaaaaaa-0000-0000-0000-000000000001")

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
        self.assertEqual(
            error.exception.message, "The GraphQL query must start with exactly `query ($device: String!)`"
        )

    def test_good_graphql_query_validate_starts_with(self):
        """Ensure clean() method returns None when valid query is sent through."""
        self.global_settings.sot_agg_query = "query ($device: String!) {devices(name:$device) {id}}"
        self.assertEqual(self.global_settings.clean(), None)
