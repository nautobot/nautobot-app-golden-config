"""Unit tests for views."""

from nautobot.apps.testing import ViewTestCases

from nautobot_golden_config import models
from nautobot_golden_config.tests import fixtures


class ComplianceFeatureViewTest(ViewTestCases.PrimaryObjectViewTestCase):
    # pylint: disable=too-many-ancestors
    """Test the ComplianceFeature views."""

    model = models.ComplianceFeature
    bulk_edit_data = {"description": "Bulk edit views"}
    form_data = {
        "name": "Test 1",
        "description": "Initial model",
    }

    update_data = {
        "name": "Test 2",
        "description": "Updated model",
    }

    @classmethod
    def setUpTestData(cls):
        fixtures.create_compliancefeature()
