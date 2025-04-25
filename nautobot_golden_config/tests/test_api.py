"""Unit tests for nautobot_golden_config."""

from nautobot.apps.testing import APIViewTestCases

from nautobot_golden_config import models
from nautobot_golden_config.tests import fixtures


class ComplianceFeatureAPIViewTest(APIViewTestCases.APIViewTestCase):
    # pylint: disable=too-many-ancestors
    """Test the API viewsets for ComplianceFeature."""

    model = models.ComplianceFeature
    # Any choice fields will require the choices_fields to be set
    # to the field names in the model that are choice fields.
    choices_fields = ()

    @classmethod
    def setUpTestData(cls):
        """Create test data for ComplianceFeature API viewset."""
        super().setUpTestData()
        # Create 3 objects for the generic API test cases.
        fixtures.create_compliancefeature()
        # Create 3 objects for the api test cases.
        cls.create_data = [
            {
                "name": "API Test One",
                "description": "Test One Description",
            },
            {
                "name": "API Test Two",
                "description": "Test Two Description",
            },
            {
                "name": "API Test Three",
                "description": "Test Three Description",
            },
        ]
        cls.update_data = {
            "name": "Update Test Two",
            "description": "Test Two Description",
        }
        cls.bulk_update_data = {
            "description": "Test Bulk Update Description",
        }
