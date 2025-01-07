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
    csv_data = (
        "name",
        "Test csv1",
        "Test csv2",
        "Test csv3",
    )

    @classmethod
    def setUpTestData(cls):
        fixtures.create_compliancefeature()
