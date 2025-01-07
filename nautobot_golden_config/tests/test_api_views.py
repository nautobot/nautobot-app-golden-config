"""Unit tests for nautobot_golden_config."""

from nautobot.apps.testing import APIViewTestCases

from nautobot_golden_config import models
from nautobot_golden_config.tests import fixtures


class ComplianceFeatureAPIViewTest(APIViewTestCases.APIViewTestCase):
    # pylint: disable=too-many-ancestors
    """Test the API viewsets for ComplianceFeature."""

    model = models.ComplianceFeature
    create_data = [
        {
            "name": "Test Model 1",
            "description": "test description",
        },
        {
            "name": "Test Model 2",
        },
    ]
    bulk_update_data = {"description": "Test Bulk Update"}

    @classmethod
    def setUpTestData(cls):
        fixtures.create_compliancefeature()
