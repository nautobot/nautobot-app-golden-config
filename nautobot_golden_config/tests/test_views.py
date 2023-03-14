"""Unit tests for nautobot_golden_config views."""

from unittest import mock

from django.test import TestCase
from django.contrib.auth import get_user_model

from nautobot.dcim.models import Device
from nautobot_golden_config import views, models

from .conftest import create_feature_rule_json, create_device_data


User = get_user_model()


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
        User.objects.create_superuser(username="views", password="incredible")
        self.client.login(username="views", password="incredible")

    def test_plot_visual_no_devices(self):

        aggr = {"comp_percents": 0, "compliants": 0, "non_compliants": 0, "total": 0}

        self.assertEqual(self.ccoh.plot_visual(aggr), None)

    @mock.patch.dict("nautobot_golden_config.tables.CONFIG_FEATURES", {"sotagg": True})
    def test_config_compliance_list_view_with_sotagg_enabled(self):
        request = self.client.get("/plugins/golden-config/golden/")
        self.assertContains(request, '<i class="mdi mdi-code-json" title="SOT Aggregate Data"></i>')

    @mock.patch.dict("nautobot_golden_config.tables.CONFIG_FEATURES", {"sotagg": False})
    def test_config_compliance_list_view_with_sotagg_disabled(self):
        request = self.client.get("/plugins/golden-config/golden/")
        self.assertNotContains(request, '<i class="mdi mdi-code-json" title="SOT Aggregate Data"></i>')

    @mock.patch.object(views, "graph_ql_query")
    @mock.patch.object(views, "get_device_to_settings_map")
    @mock.patch("nautobot_golden_config.models.GoldenConfigSetting")
    def test_config_compliance_details_sotagg_error(self, mock_gc_setting, mock_get_device_to_settings_map, mock_graphql_query):
        device =  Device.objects.first()
        mock_gc_setting.sot_agg_query = None
        mock_get_device_to_settings_map.return_value = {device.id: mock_gc_setting}
        request = self.client.get(f"/plugins/golden-config/config-compliance/details/{device.pk}/sotagg/")
        expected = '{\n    &quot;Error&quot;: &quot;No saved `GraphQL Query` query was configured in the `Golden Config Setting`&quot;\n}'
        self.assertContains(request, expected)
        mock_graphql_query.assert_not_called()

    @mock.patch.object(views, "graph_ql_query")
    @mock.patch.object(views, "get_device_to_settings_map")
    @mock.patch("nautobot_golden_config.models.GoldenConfigSetting")
    def test_config_compliance_details_sotagg_error(self, mock_gc_setting, mock_get_device_to_settings_map, mock_graph_ql_query):
        device =  Device.objects.first()
        mock_get_device_to_settings_map.return_value = {device.id: mock_gc_setting}
        mock_graph_ql_query.return_value = ("discard value", "This is a mock graphql result")
        request = self.client.get(f"/plugins/golden-config/config-compliance/details/{device.pk}/sotagg/")
        expected = "This is a mock graphql result"
        self.assertContains(request, expected)
        mock_graph_ql_query.assert_called()
