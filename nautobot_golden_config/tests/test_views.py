"""Unit tests for nautobot_golden_config views."""

from django.test import TestCase

from nautobot.dcim.models import Device
from nautobot_golden_config import views, models

from .conftest import create_feature_rule_json, create_device_data


class ConfigComplianceOverviewOverviewHelperTestCase(TestCase):
    """Test ConfigComplianceOverviewOverviewHelper."""

    def setUp(self):
        """Set up base objects."""
        create_device_data()
        dev01 = Device.objects.get(name="Device 1")
        dev02 = Device.objects.get(name="Device 2")
        dev03 = Device.objects.get(name="Device 3")
        dev04 = Device.objects.get(name="Device 4")

        feature_dev01 = create_feature_rule_json(dev01)
        feature_dev02 = create_feature_rule_json(dev02)
        feature_dev03 = create_feature_rule_json(dev03)

        updates = [
            {"device": dev01, "feature": feature_dev01},
            {"device": dev02, "feature": feature_dev02},
            {"device": dev03, "feature": feature_dev03},
            {"device": dev04, "feature": feature_dev01},
        ]
        for update in updates:
            models.ConfigCompliance.objects.create(
                device=update["device"],
                rule=update["feature"],
                actual={"foo": {"bar-1": "baz"}},
                intended={"foo": {"bar-1": "baz"}},
            )

        self.ccoh = views.ConfigComplianceOverviewOverviewHelper

    def test_plot_visual_no_devices(self):

        aggr = {"comp_percents": 0, "compliants": 0, "non_compliants": 0, "total": 0}

        self.assertEqual(self.ccoh.plot_visual(aggr), None)
