"""Unit tests for nautobot_golden_config views."""

from unittest import mock

from django.test import TestCase
from django.urls import reverse
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
    def test_config_compliance_details_sotagg_error(
        self, mock_gc_setting, mock_get_device_to_settings_map, mock_graphql_query
    ):
        device = Device.objects.first()
        mock_gc_setting.sot_agg_query = None
        mock_get_device_to_settings_map.return_value = {device.id: mock_gc_setting}
        request = self.client.get(f"/plugins/golden-config/config-compliance/details/{device.pk}/sotagg/")
        expected = "{\n    &quot;Error&quot;: &quot;No saved `GraphQL Query` query was configured in the `Golden Config Setting`&quot;\n}"
        self.assertContains(request, expected)
        mock_graphql_query.assert_not_called()

    @mock.patch.object(views, "graph_ql_query")
    @mock.patch.object(views, "get_device_to_settings_map")
    @mock.patch("nautobot_golden_config.models.GoldenConfigSetting")
    def test_config_compliance_details_sotagg_no_error(
        self, mock_gc_setting, mock_get_device_to_settings_map, mock_graph_ql_query
    ):
        device = Device.objects.first()
        mock_get_device_to_settings_map.return_value = {device.id: mock_gc_setting}
        mock_graph_ql_query.return_value = ("discard value", "This is a mock graphql result")
        request = self.client.get(f"/plugins/golden-config/config-compliance/details/{device.pk}/sotagg/")
        expected = "This is a mock graphql result"
        self.assertContains(request, expected)
        mock_graph_ql_query.assert_called()


class ConfigReplaceListViewTestCase(TestCase):
    """Test ConfigReplaceListView."""

    def setUp(self):
        """Set up base objects."""
        create_device_data()
        User.objects.create_superuser(username="views", password="incredible")
        self.client.login(username="views", password="incredible")
        self._delete_test_entry()
        models.ConfigReplace.objects.create(
            name=self._entry_name,
            platform=Device.objects.first().platform,
            description=self._entry_description,
            regex=self._entry_regex,
            replace=self._entry_replace,
        )

    @property
    def _url(self):
        return reverse("plugins:nautobot_golden_config:configreplace_list")

    def _delete_test_entry(self):
        try:
            entry = models.ConfigReplace.objects.get(name=self._entry_name)
            entry.delete()
        except models.ConfigReplace.DoesNotExist:
            pass

    @property
    def _csv_headers(self):
        return "name,platform,description,regex,replace"

    @property
    def _entry_name(self):
        return "test name"

    @property
    def _entry_description(self):
        return "test description"

    @property
    def _entry_regex(self):
        return "^startswiththeend$"

    @property
    def _entry_replace(self):
        return "<dontlookatme>"

    def test_configreplace_export(self):
        response = self.client.get(f"{self._url}?export")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["Content-Type"], "text/csv")
        last_entry = models.ConfigReplace.objects.last()
        csv_data = response.content.decode().splitlines()
        expected_last_entry = f"{last_entry.name},{last_entry.platform.id},{last_entry.description},{last_entry.regex},{last_entry.replace}"
        self.assertEqual(csv_data[0], self._csv_headers)
        self.assertEqual(csv_data[-1], expected_last_entry)
        self.assertEqual(len(csv_data) - 1, models.ConfigReplace.objects.count())

    def test_configreplace_import(self):
        self._delete_test_entry()
        platform = Device.objects.first().platform
        import_entry = (
            f"{self._entry_name},{platform.id},{self._entry_description},{self._entry_regex},{self._entry_replace}"
        )
        form_data = {"csv_data": f"{self._csv_headers}\n{import_entry}"}
        response = self.client.post(f"{self._url}import/", data=form_data, follow=True)
        last_entry = models.ConfigReplace.objects.last()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(last_entry.name, self._entry_name)
        self.assertEqual(last_entry.platform, platform)
        self.assertEqual(last_entry.description, self._entry_description)
        self.assertEqual(last_entry.regex, self._entry_regex)
        self.assertEqual(last_entry.replace, self._entry_replace)
