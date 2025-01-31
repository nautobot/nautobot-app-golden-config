"""Unit tests for nautobot_golden_config views."""

import datetime
import re
import uuid
from unittest import mock, skip

import nautobot
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.test import RequestFactory, override_settings
from django.urls import reverse
from lxml import html
from nautobot.apps.models import RestrictedQuerySet
from nautobot.apps.testing import TestCase, ViewTestCases
from nautobot.dcim.models import Device
from nautobot.extras.models import Relationship, RelationshipAssociation, Status
from nautobot.users import models as users_models
from packaging import version

from nautobot_golden_config import models, views

from .conftest import create_device_data, create_feature_rule_json, create_job_result

User = get_user_model()


@override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
class ConfigComplianceOverviewHelperTestCase(TestCase):
    """Test ConfigComplianceOverviewHelper."""

    @classmethod
    def setUpTestData(cls):
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
                intended={"foo": {"bar-2": "baz"}},
            )

        # TODO: 2.0 turn this back on.
        # cls.ccoh = views.ConfigComplianceOverviewOverviewHelper

    def test_plot_visual_no_devices(self):
        # TODO: 2.0 turn this back on.
        self.assertEqual(True, True)
        # aggr = {"comp_percents": 0, "compliants": 0, "non_compliants": 0, "total": 0}
        # self.assertEqual(self.ccoh.plot_visual(aggr), None)

    @mock.patch.dict("nautobot_golden_config.tables.CONFIG_FEATURES", {"sotagg": True})
    def test_config_compliance_list_view_with_sotagg_enabled(self):
        models.GoldenConfig.objects.create(device=Device.objects.first())
        request = self.client.get("/plugins/golden-config/golden-config/")
        self.assertContains(request, '<i class="mdi mdi-code-json" title="SOT Aggregate Data"></i>')

    @mock.patch.dict("nautobot_golden_config.tables.CONFIG_FEATURES", {"sotagg": False})
    def test_config_compliance_list_view_with_sotagg_disabled(self):
        models.GoldenConfig.objects.create(device=Device.objects.first())
        request = self.client.get("/plugins/golden-config/golden-config/")
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
        request = self.client.get(f"/plugins/golden-config/golden-config/{device.pk}/sotagg/")
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
        request = self.client.get(f"/plugins/golden-config/golden-config/{device.pk}/sotagg/")
        expected = "This is a mock graphql result"
        self.assertContains(request, expected)
        mock_graph_ql_query.assert_called()


class ConfigReplaceUIViewSetTestCase(ViewTestCases.PrimaryObjectViewTestCase):  # pylint: disable=too-many-ancestors
    """Test ConfigReplaceUIViewSet."""

    model = models.ConfigReplace

    bulk_edit_data = {
        "description": "new description",
    }

    @classmethod
    def setUpTestData(cls):
        """Set up base objects."""
        create_device_data()
        platform = Device.objects.first().platform
        for num in range(3):
            models.ConfigReplace.objects.create(
                name=f"test configreplace {num}",
                platform=platform,
                description="test description",
                regex="^(.*)$",
                replace="xyz",
            )
        cls.form_data = {
            "name": "new name",
            "platform": platform.pk,
            "description": "new description",
            "regex": "^NEW (.*)$",
            "replace": "NEW replaced text",
        }

        # For compatibility with Nautobot lower than v2.2.0
        cls.csv_data = (
            "name,regex,replace,platform",
            f"test configreplace 4,^(.*)$,xyz,{platform.pk}",
            f"test configreplace 5,^(.*)$,xyz,{platform.pk}",
            f"test configreplace 6,^(.*)$,xyz,{platform.pk}",
        )


class GoldenConfigListViewTestCase(TestCase):
    """Test GoldenConfigListView."""

    user_permissions = ["nautobot_golden_config.view_goldenconfig", "nautobot_golden_config.change_goldenconfig"]

    @classmethod
    def setUpTestData(cls):
        """Set up base objects."""
        create_device_data()
        cls.gc_settings = models.GoldenConfigSetting.objects.first()
        cls.gc_dynamic_group = cls.gc_settings.dynamic_group
        cls.gc_dynamic_group.filter = {"name": [dev.name for dev in Device.objects.all()]}
        cls.gc_dynamic_group.validated_save()
        models.GoldenConfig.objects.create(device=Device.objects.first())

    def _get_golden_config_table_header(self):
        response = self.client.get(f"{self._url}")
        html_parsed = html.fromstring(response.content.decode())
        golden_config_table = html_parsed.find_class("table")[0]
        return golden_config_table.find("thead")

    @property
    def _text_table_headers(self):
        if nautobot.__version__ >= "2.3.0":
            return ["Device", "Backup Status", "Intended Status", "Compliance Status", "Dynamic Groups", "Actions"]
        return ["Device", "Backup Status", "Intended Status", "Compliance Status", "Actions"]

    @property
    def _url(self):
        return reverse("plugins:nautobot_golden_config:goldenconfig_list")

    def test_page_ok(self):
        response = self.client.get(f"{self._url}")
        self.assertEqual(response.status_code, 200)

    def test_headers_in_table(self):
        table_header = self._get_golden_config_table_header()
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
            label="test platform to dev",
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
        table_header = self._get_golden_config_table_header()
        # xpath expression excludes the pk checkbox column (i.e. the first column)
        text_headers = [header.text_content() for header in table_header.xpath("tr/th[position()>1]")]
        # This will fail if the Relationships to Device objects showed up in the Golden Config table
        self.assertEqual(text_headers, self._text_table_headers)

    @skip("TODO: 2.0 Figure out how do csv tests.")
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
        response = self.client.get(f"{self._url}?format=csv")
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

    @skip("TODO: 2.0 Figure out how do csv tests.")
    def test_csv_export_with_filter(self):
        devices_in_site_1 = Device.objects.filter(site__name="Site 1")
        golden_config_devices = self.gc_dynamic_group.members.all()
        # Test that there are Devices in GC that are not related to Site 1
        self.assertNotEqual(devices_in_site_1, golden_config_devices)
        response = self.client.get(f"{self._url}?site={Device.objects.first().site.slug}&format=csv")
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

        not_approved_status = Status.objects.get(name="Not Approved")
        approved_status = Status.objects.get(name="Approved")

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

    @skip("TODO: 2.0 Figure out how to have pass.")
    def test_list_objects_with_constrained_permission(self):
        pass


@override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
class ConfigComplianceUIViewSetTestCase(
    ViewTestCases.BulkDeleteObjectsViewTestCase,
    # ViewTestCases.ListObjectsViewTestCase,  # generic list view tests won't work for this view since the queryset is pivoted
):
    """Test ConfigComplianceUIViewSet views."""

    model = models.ConfigCompliance

    @classmethod
    def setUpTestData(cls):
        create_device_data()
        dev01 = Device.objects.get(name="Device 1")
        dev02 = Device.objects.get(name="Device 2")
        dev03 = Device.objects.get(name="Device 3")
        dev04 = Device.objects.get(name="Device 4")

        for iterator_i in range(4):
            feature_dev01 = create_feature_rule_json(dev01, feature=f"TestFeature{iterator_i}")
            feature_dev02 = create_feature_rule_json(dev02, feature=f"TestFeature{iterator_i}")
            feature_dev03 = create_feature_rule_json(dev03, feature=f"TestFeature{iterator_i}")

            updates = [
                {"device": dev01, "feature": feature_dev01},
                {"device": dev02, "feature": feature_dev02},
                {"device": dev03, "feature": feature_dev03},
                {"device": dev04, "feature": feature_dev01},
            ]
            for iterator_j, update in enumerate(updates):
                compliance_int = iterator_j % 2
                models.ConfigCompliance.objects.create(
                    device=update["device"],
                    rule=update["feature"],
                    actual={"foo": {"bar-1": "baz"}},
                    intended={"foo": {f"bar-{compliance_int}": "baz"}},
                    compliance=bool(compliance_int),
                    compliance_int=compliance_int,
                )

    def test_alter_queryset(self):
        """Test alter_queryset method returns the expected pivoted queryset."""

        unused_features = (
            models.ComplianceFeature.objects.create(slug="unused-feature-1", name="Unused Feature 1"),
            models.ComplianceFeature.objects.create(slug="unused-feature-2", name="Unused Feature 2"),
        )
        request = RequestFactory(SERVER_NAME="nautobot.example.com").get(
            reverse("plugins:nautobot_golden_config:configcompliance_list")
        )
        request.user = self.user
        queryset = views.ConfigComplianceUIViewSet(request=request).alter_queryset(request)
        features = (
            models.ComplianceFeature.objects.filter(feature__rule__isnull=False)
            .values_list("slug", flat=True)
            .distinct()
        )
        self.assertNotIn(unused_features[0].slug, features)
        self.assertNotIn(unused_features[1].slug, features)
        self.assertGreater(len(features), 0)
        self.assertIsInstance(queryset, RestrictedQuerySet)
        for device in queryset:
            self.assertSequenceEqual(list(device.keys()), ["device", "device__name", *features])
            for feature in features:
                self.assertIn(device[feature], [0, 1])

    def test_table_columns(self):
        """Test the columns of the ConfigCompliance table return the expected pivoted data."""
        response = self.client.get(reverse("plugins:nautobot_golden_config:configcompliance_list"))
        expected_table_headers = ["Device", "TestFeature0", "TestFeature1", "TestFeature2", "TestFeature3"]
        table_headers = re.findall(r'<th class="orderable"><a href=.*>(.+)</a></th>', response.content.decode())
        self.assertEqual(table_headers, expected_table_headers)

        # Add a new compliance feature and ensure the table headers update correctly
        device2 = Device.objects.get(name="Device 2")
        new_compliance_feature = create_feature_rule_json(device2, feature="NewTestFeature")
        models.ConfigCompliance.objects.create(
            device=device2,
            rule=new_compliance_feature,
            actual={"foo": {"bar-1": "baz"}},
            intended={"foo": {"bar-1": "baz"}},
            compliance=True,
            compliance_int=1,
        )

        response = self.client.get(reverse("plugins:nautobot_golden_config:configcompliance_list"))
        expected_table_headers = [
            "Device",
            "TestFeature0",
            "TestFeature1",
            "TestFeature2",
            "TestFeature3",
            "NewTestFeature",
        ]
        table_headers = re.findall(r'<th class="orderable"><a href=.*>(.+)</a></th>', response.content.decode())
        self.assertEqual(table_headers, expected_table_headers)

        # Remove compliance features and ensure the table headers update correctly
        models.ConfigCompliance.objects.filter(rule__feature__name__in=["TestFeature0", "TestFeature1"]).delete()

        response = self.client.get(reverse("plugins:nautobot_golden_config:configcompliance_list"))
        expected_table_headers = ["Device", "TestFeature2", "TestFeature3", "NewTestFeature"]
        table_headers = re.findall(r'<th class="orderable"><a href=.*>(.+)</a></th>', response.content.decode())
        self.assertEqual(table_headers, expected_table_headers)

    def test_bulk_delete_form_contains_all_objects(self):  # pylint: disable=inconsistent-return-statements
        if version.parse(settings.VERSION) < version.parse("2.3.11") and hasattr(
            super(), "test_bulk_delete_form_contains_all_objects"
        ):
            return super().test_bulk_delete_form_contains_all_objects()  # pylint: disable=no-member
        self.skipTest(
            "Golden config uses an older version of the bulk delete views that does not support tests introduced in 2.3.11"
        )

    def test_bulk_delete_form_contains_all_filtered(self):  # pylint: disable=inconsistent-return-statements
        if version.parse(settings.VERSION) < version.parse("2.3.11") and hasattr(
            super(), "test_bulk_delete_form_contains_all_filtered"
        ):
            return super().test_bulk_delete_form_contains_all_filtered()  # pylint: disable=no-member
        self.skipTest(
            "Golden config uses an older version of the bulk delete views that does not support tests introduced in 2.3.11"
        )

    # Copied from https://github.com/nautobot/nautobot/blob/3dbd4248f9dcbab69767a357a635490a28a24e0b/nautobot/core/testing/views.py
    # Golden config uses an older version of the bulk delete views that does not support tests introduced in 2.3.11
    @override_settings(EXEMPT_VIEW_PERMISSIONS=[])
    def test_bulk_delete_objects_with_constrained_permission(self):
        pk_list = self.get_deletable_object_pks()
        initial_count = self._get_queryset().count()
        data = {
            "pk": pk_list,
            "confirm": True,
            "_confirm": True,  # Form button
        }

        # Assign constrained permission
        obj_perm = users_models.ObjectPermission(
            name="Test permission",
            constraints={"pk": str(uuid.uuid4())},  # Match a non-existent pk (i.e., deny all)
            actions=["delete"],
        )
        obj_perm.save()
        obj_perm.users.add(self.user)
        obj_perm.object_types.add(ContentType.objects.get_for_model(self.model))

        # Attempt to bulk delete non-permitted objects
        self.assertHttpStatus(self.client.post(self._get_url("bulk_delete"), data), 302)
        self.assertEqual(self._get_queryset().count(), initial_count)

        # Update permission constraints
        obj_perm.constraints = {"pk__isnull": False}  # Match a non-existent pk (i.e., allow all)
        obj_perm.save()

        # Bulk delete permitted objects
        self.assertHttpStatus(self.client.post(self._get_url("bulk_delete"), data), 302)
        self.assertEqual(self._get_queryset().count(), initial_count - len(pk_list))

    # Copied from https://github.com/nautobot/nautobot/blob/3dbd4248f9dcbab69767a357a635490a28a24e0b/nautobot/core/testing/views.py
    # Golden config uses an older version of the bulk delete views that does not support tests introduced in 2.3.11
    @override_settings(EXEMPT_VIEW_PERMISSIONS=[])
    def test_bulk_delete_objects_with_permission(self):
        pk_list = self.get_deletable_object_pks()
        initial_count = self._get_queryset().count()
        data = {
            "pk": pk_list,
            "confirm": True,
            "_confirm": True,  # Form button
        }

        # Assign unconstrained permission
        self.add_permissions(f"{self.model._meta.app_label}.delete_{self.model._meta.model_name}")

        # Try POST with model-level permission
        self.assertHttpStatus(self.client.post(self._get_url("bulk_delete"), data), 302)
        self.assertEqual(self._get_queryset().count(), initial_count - len(pk_list))
