"""Unit tests for nautobot_golden_config views."""

import datetime
from unittest import mock, skipIf

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.urls import reverse
from lxml import html
from nautobot.dcim.models import Device
from nautobot.extras.models import Relationship, RelationshipAssociation, Status
from nautobot.utilities.testing import ViewTestCases
from packaging import version

from nautobot_golden_config import models, views

from .conftest import create_device_data, create_feature_rule_json, create_job_result

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
        expected_last_entry = f"{last_entry.name},{last_entry.platform.slug},{last_entry.description},{last_entry.regex},{last_entry.replace}"
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


class GoldenConfigListViewTestCase(TestCase):
    """Test GoldenConfigListView."""

    def setUp(self):
        """Set up base objects."""
        create_device_data()
        User.objects.create_superuser(username="views", password="incredible")
        self.client.login(username="views", password="incredible")
        self.gc_settings = models.GoldenConfigSetting.objects.first()
        self.gc_dynamic_group = self.gc_settings.dynamic_group
        self.gc_dynamic_group.filter = {"name": [dev.name for dev in Device.objects.all()]}
        self.gc_dynamic_group.validated_save()

    def _get_golden_config_table(self):
        response = self.client.get(f"{self._url}")
        html_parsed = html.fromstring(response.content.decode())
        golden_config_table = html_parsed.find_class("table")[0]
        return golden_config_table.iterchildren()

    @property
    def _text_table_headers(self):
        return ["Device", "Backup Status", "Intended Status", "Compliance Status", "Actions"]

    @property
    def _url(self):
        return reverse("plugins:nautobot_golden_config:goldenconfig_list")

    def test_page_ok(self):
        response = self.client.get(f"{self._url}")
        self.assertEqual(response.status_code, 200)

    def test_headers_in_table(self):
        table_header, _ = self._get_golden_config_table()
        headers = table_header.iterdescendants("th")
        checkbox_header = next(headers)
        checkbox_element = checkbox_header.find("input")
        self.assertEqual(checkbox_element.type, "checkbox")
        text_headers = [header.text_content() for header in headers]
        self.assertEqual(text_headers, self._text_table_headers)

    def test_device_relationship_not_included_in_golden_config_table(self):
        # Create a RelationshipAssociation to Device Model to setup test case
        device_content_type = ContentType.objects.get_for_model(Device)
        platform_content_type = ContentType.objects.get(app_label="dcim", model="platform")
        device = Device.objects.first()
        relationship = Relationship.objects.create(
            name="test platform to dev",
            type="one-to-many",
            source_type_id=platform_content_type.id,
            destination_type_id=device_content_type.id,
        )
        RelationshipAssociation.objects.create(
            source_type_id=platform_content_type.id,
            source_id=device.platform.id,
            destination_type_id=device_content_type.id,
            destination_id=device.id,
            relationship_id=relationship.id,
        )
        table_header, _ = self._get_golden_config_table()
        # xpath expression excludes the pk checkbox column (i.e. the first column)
        text_headers = [header.text_content() for header in table_header.xpath("tr/th[position()>1]")]
        # This will fail if the Relationships to Device objects showed up in the Golden Config table
        self.assertEqual(text_headers, self._text_table_headers)

    def test_table_entries_based_on_dynamic_group_scope(self):
        self.assertEqual(models.GoldenConfig.objects.count(), 0)
        _, table_body = self._get_golden_config_table()
        devices_in_table = [device_column.text for device_column in table_body.xpath("tr/td[2]/a")]
        device_names = [device.name for device in self.gc_dynamic_group.members]
        self.assertEqual(devices_in_table, device_names)

    def test_scope_change_affects_table_entries(self):
        last_device = self.gc_dynamic_group.members.last()
        _, table_body = self._get_golden_config_table()
        devices_in_table = [device_column.text for device_column in table_body.xpath("tr/td[2]/a")]
        self.assertIn(last_device.name, devices_in_table)
        self.gc_dynamic_group.filter["name"] = [dev.name for dev in Device.objects.exclude(pk=last_device.pk)]
        self.gc_dynamic_group.validated_save()
        _, table_body = self._get_golden_config_table()
        devices_in_table = [device_column.text for device_column in table_body.xpath("tr/td[2]/a")]
        self.assertNotIn(last_device.name, devices_in_table)

    def test_csv_export(self):
        # verify GoldenConfig table is empty
        self.assertEqual(models.GoldenConfig.objects.count(), 0)
        intended_datetime = datetime.datetime.now()
        first_device = self.gc_dynamic_group.members.first()
        models.GoldenConfig.objects.create(
            device=first_device,
            intended_last_attempt_date=intended_datetime,
            intended_last_success_date=intended_datetime,
        )
        response = self.client.get(f"{self._url}?export")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["Content-Type"], "text/csv")
        csv_data = response.content.decode().splitlines()
        csv_headers = "Device Name,backup attempt,backup successful,intended attempt,intended successful,compliance attempt,compliance successful"
        self.assertEqual(csv_headers, csv_data[0])
        intended_datetime_formated = intended_datetime.strftime("%Y-%m-%dT%H:%M:%S.%f+00:00")
        # Test single entry in GoldenConfig table has data
        expected_first_row = f"{first_device.name},,,{intended_datetime_formated},{intended_datetime_formated},,"
        self.assertEqual(expected_first_row, csv_data[1])
        # Test Devices in scope but without entries in GoldenConfig have empty entries
        empty_csv_rows = [
            f"{device.name},,,,,," for device in self.gc_dynamic_group.members.exclude(pk=first_device.pk)
        ]
        self.assertEqual(empty_csv_rows, csv_data[2:])

    def test_csv_export_with_filter(self):
        devices_in_site_1 = Device.objects.filter(site__name="Site 1")
        golden_config_devices = self.gc_dynamic_group.members.all()
        # Test that there are Devices in GC that are not related to Site 1
        self.assertNotEqual(devices_in_site_1, golden_config_devices)
        response = self.client.get(f"{self._url}?site={Device.objects.first().site.slug}&export")
        self.assertEqual(response.status_code, 200)
        csv_data = response.content.decode().splitlines()
        device_names_in_export = [entry.split(",")[0] for entry in csv_data[1:]]
        device_names_in_site_1 = [device.name for device in devices_in_site_1]
        self.assertEqual(device_names_in_export, device_names_in_site_1)


# pylint: disable=too-many-ancestors,too-many-locals
class ConfigPlanTestCase(
    ViewTestCases.GetObjectViewTestCase,
    ViewTestCases.GetObjectChangelogViewTestCase,
    ViewTestCases.ListObjectsViewTestCase,
    # Disabling Create tests because ConfigPlans are created via Job
    # ViewTestCases.CreateObjectViewTestCase,
    ViewTestCases.DeleteObjectViewTestCase,
    ViewTestCases.EditObjectViewTestCase,
):
    """Test ConfigPlan views."""

    model = models.ConfigPlan

    @classmethod
    def setUpTestData(cls):
        create_device_data()
        device1 = Device.objects.get(name="Device 1")
        device2 = Device.objects.get(name="Device 2")
        device3 = Device.objects.get(name="Device 3")

        rule1 = create_feature_rule_json(device1, feature="Test Feature 1")
        rule2 = create_feature_rule_json(device2, feature="Test Feature 2")
        rule3 = create_feature_rule_json(device3, feature="Test Feature 3")
        rule4 = create_feature_rule_json(device3, feature="Test Feature 4")

        job_result1 = create_job_result()
        job_result2 = create_job_result()
        job_result3 = create_job_result()

        not_approved_status = Status.objects.get(slug="not-approved")
        approved_status = Status.objects.get(slug="approved")

        plan1 = models.ConfigPlan.objects.create(
            device=device1,
            plan_type="intended",
            config_set="Test Config Set 1",
            change_control_id="Test Change Control ID 1",
            change_control_url="https://1.example.com/",
            status=not_approved_status,
            plan_result_id=job_result1.id,
        )
        plan1.feature.add(rule1.feature)
        plan1.validated_save()
        plan2 = models.ConfigPlan.objects.create(
            device=device2,
            plan_type="missing",
            config_set="Test Config Set 2",
            change_control_id="Test Change Control ID 2",
            change_control_url="https://2.example.com/",
            status=not_approved_status,
            plan_result_id=job_result2.id,
        )
        plan2.feature.add(rule2.feature)
        plan2.validated_save()
        plan3 = models.ConfigPlan.objects.create(
            device=device3,
            plan_type="remediation",
            config_set="Test Config Set 3",
            change_control_id="Test Change Control ID 3",
            change_control_url="https://3.example.com/",
            status=not_approved_status,
            plan_result_id=job_result3.id,
        )
        plan3.feature.set([rule3.feature, rule4.feature])
        plan3.validated_save()

        # Used for EditObjectViewTestCase
        cls.form_data = {
            "change_control_id": "Test Change Control ID 4",
            "change_control_url": "https://4.example.com/",
            "status": approved_status.pk,
        }

    @skipIf(version.parse(settings.VERSION) <= version.parse("1.5.5"), "Bug in 1.5.4 and below")
    def test_list_objects_with_permission(self):
        """Overriding test for versions < 1.5.5."""
        super().test_list_objects_with_permission()
