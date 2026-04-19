"""Unit tests for nautobot_golden_config views."""
# pylint: disable=protected-access,too-many-lines

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
from nautobot.core.utils import lookup
from nautobot.core.views.mixins import PERMISSIONS_ACTION_MAP, NautobotViewSetMixin
from nautobot.dcim.models import Device
from nautobot.extras.models import DynamicGroup, Status
from nautobot.users import models as users_models
from packaging import version

from nautobot_golden_config import models, tables, views
from nautobot_golden_config.utilities.constant import PLUGIN_CFG

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
        request = self.client.get("/plugins/golden-config/golden-config/", headers={"HX-Request": "true"})
        self.assertContains(request, '<span class="mdi mdi-code-json" title="SOT Aggregate Data"></span>')

    @mock.patch.dict("nautobot_golden_config.tables.CONFIG_FEATURES", {"sotagg": False})
    def test_config_compliance_list_view_with_sotagg_disabled(self):
        models.GoldenConfig.objects.create(device=Device.objects.first())
        request = self.client.get("/plugins/golden-config/golden-config/")
        self.assertNotContains(request, '<span class="mdi mdi-code-json" title="SOT Aggregate Data"></span>')

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
        cls.gc_dynamic_group = DynamicGroup.objects.create(
            name="GoldenConfig Default Group",
            filter={},
            content_type=ContentType.objects.get_for_model(Device),
        )
        cls.gc_settings = models.GoldenConfigSetting.objects.create(dynamic_group=cls.gc_dynamic_group)
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

    # TODO: 3.0.0 Followup on whether these tests are required in Nautobot 3.0.0
    # def test_headers_in_table(self):
    #     table_header = self._get_golden_config_table_header()
    #     headers = table_header.iterdescendants("th")
    #     checkbox_header = next(headers)
    #     checkbox_element = checkbox_header.find("input")
    #     self.assertEqual(checkbox_element.type, "checkbox")
    #     text_headers = [header.text_content() for header in headers]
    #     self.assertEqual(text_headers, self._text_table_headers)

    # def test_device_relationship_not_included_in_golden_config_table(self):
    #     # Create a RelationshipAssociation to Device Model to setup test case
    #     device_content_type = ContentType.objects.get_for_model(Device)
    #     platform_content_type = ContentType.objects.get(app_label="dcim", model="platform")
    #     device = Device.objects.first()
    #     relationship = Relationship.objects.create(
    #         label="test platform to dev",
    #         type="one-to-many",
    #         source_type_id=platform_content_type.id,
    #         destination_type_id=device_content_type.id,
    #     )
    #     RelationshipAssociation.objects.create(
    #         source_type_id=platform_content_type.id,
    #         source_id=device.platform.id,
    #         destination_type_id=device_content_type.id,
    #         destination_id=device.id,
    #         relationship_id=relationship.id,
    #     )
    #     table_header = self._get_golden_config_table_header()
    #     # xpath expression excludes the pk checkbox column (i.e. the first column)
    #     text_headers = [header.text_content() for header in table_header.xpath("tr/th[position()>1]")]
    #     # This will fail if the Relationships to Device objects showed up in the Golden Config table
    #     self.assertEqual(text_headers, self._text_table_headers)

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
    allowed_number_of_tree_queries_per_view_type = {
        "retrieve": 1,
    }

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
            "change_control_url": "https://example.com/?" + "x" * 1000,
            "status": approved_status.pk,
        }
        PLUGIN_CFG["postprocessing_subscribed"] = ["whatever"]

    @skip("TODO: 2.0 Figure out how to have pass.")
    def test_list_objects_with_constrained_permission(self):
        pass


@override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
class ConfigComplianceUIViewSetTestCase(
    ViewTestCases.BulkDeleteObjectsViewTestCase,
    ViewTestCases.GetObjectViewTestCase,
    # ViewTestCases.ListObjectsViewTestCase,  # generic list view tests won't work for this view since the queryset is pivoted
):
    """Test ConfigComplianceUIViewSet views."""

    model = models.ConfigCompliance
    allowed_number_of_tree_queries_per_view_type = {"retrieve": 1}
    custom_action_required_permissions = {
        "plugins:nautobot_golden_config:configcompliance_overview": ["nautobotgoldenconfig.view_configcompliance"],
        "plugins:nautobot_golden_config:configcompliance_devicetab": ["nautobotgoldenconfig.view_configcompliance"],
    }

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
                is_compliant = iterator_j % 2
                models.ConfigCompliance.objects.create(
                    device=update["device"],
                    rule=update["feature"],
                    actual={"foo": {"bar-1": "baz"}},
                    intended={"foo": {f"bar-{is_compliant}": "baz"}},
                    compliance=bool(is_compliant),
                )

    def test_get_object_anonymous(self):
        # TODO: remove when ConfigComplianceUIViewSet has Change Log
        self.assertEqual(True, True)

    @override_settings(EXEMPT_VIEW_PERMISSIONS=[])
    def test_custom_actions(self):
        """
        Copied from nautobot generic test to skip device tab custom action.
        """
        base_view = lookup.get_view_for_model(self.model)
        if not issubclass(base_view, NautobotViewSetMixin):
            self.skipTest(f"View {base_view} is not using NautobotUIViewSet")

        instance = self._get_queryset().first()
        for action_func in base_view.get_extra_actions():
            if action_func.__name__ == "devicetab":
                # TODO: devicetab should be implemented as a template extension
                continue
            if not action_func.detail:
                continue
            if "get" not in action_func.mapping:
                continue
            if action_func.url_name == "data-compliance" and not getattr(base_view, "object_detail_content", None):
                continue
            with self.subTest(action=action_func.url_name):
                if action_func.url_name in self.custom_action_required_permissions:
                    required_permissions = self.custom_action_required_permissions[action_func.url_name]
                else:
                    base_action = action_func.kwargs.get("custom_view_base_action")
                    if base_action is None:
                        if action_func.__name__ not in PERMISSIONS_ACTION_MAP:
                            self.fail(f"Missing custom_view_base_action for action {action_func.__name__}")
                        base_action = PERMISSIONS_ACTION_MAP[action_func.__name__]

                    required_permissions = [f"{self.model._meta.app_label}.{base_action}_{self.model._meta.model_name}"]
                    required_permissions += action_func.kwargs.get("custom_view_additional_permissions", [])

                try:
                    url = self._get_url(action_func.url_name, instance)
                    self.assertHttpStatus(self.client.get(url), [403, 404])
                    for permission in required_permissions[:-1]:
                        self.add_permissions(permission)
                        self.assertHttpStatus(self.client.get(url), [403, 404])

                    self.add_permissions(required_permissions[-1])
                    self.assertHttpStatus(self.client.get(url, follow=True), 200)
                finally:
                    # delete the permissions here so that we start from a clean slate on the next loop
                    self.remove_permissions(*required_permissions)

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
        queryset = views.ConfigComplianceUIViewSet(request=request, action="list").alter_queryset(request)
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
            self.assertCountEqual(list(device.keys()), ["device", "device__name", *features])
            for feature in features:
                self.assertIn(device[feature], ["True", "False"])

    def test_table_columns(self):
        """Test the columns of the ConfigCompliance table return the expected pivoted data."""
        response = self.client.get(reverse("plugins:nautobot_golden_config:configcompliance_list"))
        expected_table_headers = ["Device", "TestFeature0", "TestFeature1", "TestFeature2", "TestFeature3"]
        table_headers = [
            h.strip()
            for h in re.findall(r'<th class="orderable"><a href=[^>]*>([^<]+)</a></th>', response.content.decode())
        ]
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
        table_headers = [
            h.strip()
            for h in re.findall(r'<th class="orderable"><a href=[^>]*>([^<]+)</a></th>', response.content.decode())
        ]
        self.assertEqual(table_headers, expected_table_headers)

        # Remove compliance features and ensure the table headers update correctly
        models.ConfigCompliance.objects.filter(rule__feature__name__in=["TestFeature0", "TestFeature1"]).delete()

        response = self.client.get(reverse("plugins:nautobot_golden_config:configcompliance_list"))
        expected_table_headers = ["Device", "TestFeature2", "TestFeature3", "NewTestFeature"]
        table_headers = [
            h.strip()
            for h in re.findall(r'<th class="orderable"><a href=[^>]*>([^<]+)</a></th>', response.content.decode())
        ]
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

    def test_overview_status_and_context(self):
        """The overview action returns HTTP 200 and populates expected context keys."""
        url = reverse("plugins:nautobot_golden_config:configcompliance_overview")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("table", response.context)
        self.assertIn("bar_chart_panel", response.context)
        self.assertIn("filter_form", response.context)

    def test_overview_per_feature_counts(self):
        """Annotation values on the overview queryset match the fixture data.

        setUpTestData creates 4 devices x 4 features with compliance alternating
        0/1/0/1 per device, so each feature should be: count=4, compliant=2,
        non_compliant=2, comp_percent=50.0.
        """
        url = reverse("plugins:nautobot_golden_config:configcompliance_overview")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        all_device_ids = list(models.ConfigCompliance.objects.values_list("device_id", flat=True).distinct())
        feature_qs = views._get_feature_compliance_queryset(all_device_ids)
        for record in feature_qs:
            self.assertEqual(record.count, 4, msg=f"count mismatch for {record.slug}")
            self.assertEqual(record.compliant, 2, msg=f"compliant mismatch for {record.slug}")
            self.assertEqual(record.non_compliant, 2, msg=f"non_compliant mismatch for {record.slug}")
            self.assertAlmostEqual(record.comp_percent, 50.0, msg=f"comp_percent mismatch for {record.slug}")


@override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
class FeatureComplianceQuerysetTestCase(TestCase):
    """Unit tests for views._get_feature_compliance_queryset."""

    @classmethod
    def setUpTestData(cls):
        create_device_data()
        # Device 1 and Device 4 share Platform 1 — one rule covers both.
        cls.dev1 = Device.objects.get(name="Device 1")
        cls.dev4 = Device.objects.get(name="Device 4")
        cls.rule = create_feature_rule_json(cls.dev1, feature="qset-feat-a")

    def _create_compliance(self, device, rule, compliant):
        # save() recalculates compliance via FUNC_MAPPER(actual, intended).
        # Drive the result through actual/intended: matching = compliant, differing = non-compliant.
        actual = {"foo": "bar"}
        intended = {"foo": "bar"} if compliant else {"foo": "baz"}
        return models.ConfigCompliance.objects.create(
            device=device,
            rule=rule,
            actual=actual,
            intended=intended,
        )

    def test_all_compliant(self):
        """All devices compliant returns 100%."""
        self._create_compliance(self.dev1, self.rule, 1)
        self._create_compliance(self.dev4, self.rule, 1)
        result = views._get_feature_compliance_queryset([self.dev1.id, self.dev4.id]).get(slug="qset-feat-a")
        self.assertEqual(result.count, 2)
        self.assertEqual(result.compliant, 2)
        self.assertEqual(result.non_compliant, 0)
        self.assertAlmostEqual(result.comp_percent, 100.0)

    def test_all_non_compliant(self):
        """All devices non-compliant returns 0%."""
        self._create_compliance(self.dev1, self.rule, 0)
        self._create_compliance(self.dev4, self.rule, 0)
        result = views._get_feature_compliance_queryset([self.dev1.id, self.dev4.id]).get(slug="qset-feat-a")
        self.assertEqual(result.count, 2)
        self.assertEqual(result.compliant, 0)
        self.assertEqual(result.non_compliant, 2)
        self.assertAlmostEqual(result.comp_percent, 0.0)

    def test_mixed_compliance(self):
        """Count should be 2, compliant=1, non_compliant=1, comp_percent=50.0."""
        self._create_compliance(self.dev1, self.rule, 1)
        self._create_compliance(self.dev4, self.rule, 0)
        result = views._get_feature_compliance_queryset([self.dev1.id, self.dev4.id]).get(slug="qset-feat-a")
        self.assertEqual(result.count, 2)
        self.assertEqual(result.compliant, 1)
        self.assertEqual(result.non_compliant, 1)
        self.assertAlmostEqual(result.comp_percent, 50.0)

    def test_empty_device_ids_gives_zero_count_and_null_percent(self):
        """Passing an empty list returns count=0 and comp_percent=None (no division by zero)."""
        self._create_compliance(self.dev1, self.rule, 1)
        result = views._get_feature_compliance_queryset([]).get(slug="qset-feat-a")
        self.assertEqual(result.count, 0)
        self.assertIsNone(result.comp_percent)

    def test_filtering_excludes_out_of_scope_devices(self):
        """Only devices whose IDs are in device_ids contribute to the counts."""
        self._create_compliance(self.dev1, self.rule, 1)  # included
        self._create_compliance(self.dev4, self.rule, 0)  # excluded
        result = views._get_feature_compliance_queryset([self.dev1.id]).get(slug="qset-feat-a")
        self.assertEqual(result.count, 1)
        self.assertEqual(result.compliant, 1)
        self.assertEqual(result.non_compliant, 0)
        self.assertAlmostEqual(result.comp_percent, 100.0)

    def test_feature_with_no_compliance_records_has_null_percent(self):
        """A feature whose rule has no ConfigCompliance entries returns count=0, comp_percent=None."""
        result = views._get_feature_compliance_queryset([self.dev1.id]).get(slug="qset-feat-a")
        self.assertEqual(result.count, 0)
        self.assertIsNone(result.comp_percent)

    def test_ordering_by_comp_percent_descending(self):
        """Features are ordered highest comp_percent first."""
        dev2 = Device.objects.get(name="Device 2")  # Platform 2 — separate rule needed
        rule_b = create_feature_rule_json(dev2, feature="qset-feat-b")
        self._create_compliance(self.dev1, self.rule, 1)  # feat-a: 100%
        self._create_compliance(dev2, rule_b, 0)  # feat-b: 0%
        slugs = list(
            views._get_feature_compliance_queryset([self.dev1.id, dev2.id])
            .filter(slug__in=["qset-feat-a", "qset-feat-b"])
            .values_list("slug", flat=True)
        )
        self.assertEqual(slugs, ["qset-feat-a", "qset-feat-b"])

    def test_na_records_excluded_from_compliant_counts(self):
        """N/A + compliant: N/A excluded from count, compliant counted, comp_percent reflects only real records."""
        self._create_compliance(self.dev1, self.rule, 1)
        cc_na = self._create_compliance(self.dev4, self.rule, 1)
        models.ConfigCompliance.objects.filter(pk=cc_na.pk).update(compliance=None)

        result = views._get_feature_compliance_queryset([self.dev1.id, self.dev4.id]).get(slug="qset-feat-a")
        self.assertEqual(result.count, 1)
        self.assertEqual(result.compliant, 1)
        self.assertEqual(result.non_compliant, 0)
        self.assertAlmostEqual(result.comp_percent, 100.0)

    def test_na_records_excluded_from_non_compliant_counts(self):
        """N/A + non-compliant: N/A excluded, non-compliant counted."""
        self._create_compliance(self.dev1, self.rule, 0)
        cc_na = self._create_compliance(self.dev4, self.rule, 1)
        models.ConfigCompliance.objects.filter(pk=cc_na.pk).update(compliance=None)

        result = views._get_feature_compliance_queryset([self.dev1.id, self.dev4.id]).get(slug="qset-feat-a")
        self.assertEqual(result.count, 1)
        self.assertEqual(result.compliant, 0)
        self.assertEqual(result.non_compliant, 1)
        self.assertAlmostEqual(result.comp_percent, 0.0)

    def test_all_na_gives_zero_count_and_null_percent(self):
        """All records N/A: count=0, comp_percent=None (same as no records)."""
        cc1 = self._create_compliance(self.dev1, self.rule, 1)
        cc2 = self._create_compliance(self.dev4, self.rule, 1)
        models.ConfigCompliance.objects.filter(pk__in=[cc1.pk, cc2.pk]).update(compliance=None)

        result = views._get_feature_compliance_queryset([self.dev1.id, self.dev4.id]).get(slug="qset-feat-a")
        self.assertEqual(result.count, 0)
        self.assertEqual(result.compliant, 0)
        self.assertEqual(result.non_compliant, 0)
        self.assertIsNone(result.comp_percent)

    def test_mixed_compliance_with_na(self):
        """Compliant + non-compliant + N/A: N/A excluded, others counted normally."""
        dev2 = Device.objects.get(name="Device 2")
        rule_b = create_feature_rule_json(dev2, feature="qset-feat-mixed")
        self._create_compliance(self.dev1, self.rule, 1)
        self._create_compliance(self.dev4, self.rule, 0)
        cc_na = self._create_compliance(dev2, rule_b, 1)
        models.ConfigCompliance.objects.filter(pk=cc_na.pk).update(compliance=None)

        result = views._get_feature_compliance_queryset([self.dev1.id, self.dev4.id, dev2.id]).get(slug="qset-feat-a")
        self.assertEqual(result.count, 2)
        self.assertEqual(result.compliant, 1)
        self.assertEqual(result.non_compliant, 1)
        self.assertAlmostEqual(result.comp_percent, 50.0)


@override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
class PivotQueryMatrixTestCase(TestCase):  # pylint: disable=too-many-public-methods
    """Test the hand-built pivot query (alter_queryset) against the full behavior matrix.

    Per-cell values:
        True  → 1 in pivot (green check)
        False → 0 in pivot (red X)
        None  → filtered out (N/A)
        (no record) → None in pivot (default dash)

    Per-device row scenarios:
        1. All features compliant
        2. All features non-compliant
        3. Mixed compliant/non-compliant
        4. All features N/A → device excluded from pivot
        5. Mix of real compliance + N/A
        6. No records at all → device not in pivot
        7. Some features have records, some don't
        8. N/A + no-record mix → device excluded
        9. Real + N/A + no-record
    """

    @classmethod
    def setUpTestData(cls):
        create_device_data()
        cls.dev1 = Device.objects.get(name="Device 1")
        cls.dev2 = Device.objects.get(name="Device 2")
        cls.dev3 = Device.objects.get(name="Device 3")
        cls.dev4 = Device.objects.get(name="Device 4")
        cls.dev5 = Device.objects.get(name="Device 5")
        cls.dev6 = Device.objects.get(name="Device 6")

        # Create 3 features on Platform 1 (shared by dev1, dev4, dev5, dev6)
        cls.feat_bgp = create_feature_rule_json(cls.dev1, feature="bgp")
        cls.feat_ntp = create_feature_rule_json(cls.dev1, feature="ntp")
        cls.feat_snmp = create_feature_rule_json(cls.dev1, feature="snmp")

    def _get_pivot(self):
        """Execute the pivot query and return {device_name: {feature: value}}."""
        request = RequestFactory(SERVER_NAME="nautobot.example.com").get(
            reverse("plugins:nautobot_golden_config:configcompliance_list")
        )
        request.user = User.objects.first()
        qs = views.ConfigComplianceUIViewSet(request=request, action="list").alter_queryset(request)
        return {row["device__name"]: row for row in qs}

    def _create(self, device, rule, compliant):
        """Create a ConfigCompliance record with the given compliance result."""
        actual = {"foo": "bar"}
        intended = {"foo": "bar"} if compliant else {"foo": "baz"}
        return models.ConfigCompliance.objects.create(device=device, rule=rule, actual=actual, intended=intended)

    def _mark_na(self, cc):
        """Mark a ConfigCompliance record as N/A by setting compliance to None."""
        models.ConfigCompliance.objects.filter(pk=cc.pk).update(compliance=None)

    # --- Per-cell values ---

    def test_render_compliant(self):
        """ComplianceColumn renders a green check for compliant."""
        col = tables.ComplianceColumn(verbose_name="test")
        rendered = col.render("True")
        self.assertIn("mdi-check-bold", rendered)
        self.assertIn("text-success", rendered)

    def test_render_non_compliant(self):
        """ComplianceColumn renders a red X for non-compliant."""
        col = tables.ComplianceColumn(verbose_name="test")
        rendered = col.render("False")
        self.assertIn("mdi-close-thick", rendered)
        self.assertIn("text-danger", rendered)

    def test_render_na(self):
        """ComplianceColumn renders double-dash for N/A."""
        col = tables.ComplianceColumn(verbose_name="test")
        rendered = col.render("None")
        self.assertIn("- -", rendered)
        self.assertIn("N/A", rendered)

    def test_render_no_record(self):
        """ComplianceColumn renders a dash for no record."""
        col = tables.ComplianceColumn(verbose_name="test")
        rendered = col.render(None)
        self.assertIn("mdi-minus", rendered)

    def test_cell_compliant(self):
        """True compliance → "True" in pivot."""
        self._create(self.dev1, self.feat_bgp, True)
        pivot = self._get_pivot()
        self.assertEqual(pivot["Device 1"]["bgp"], "True")

    def test_cell_non_compliant(self):
        """False compliance → "False" in pivot."""
        self._create(self.dev1, self.feat_bgp, False)
        pivot = self._get_pivot()
        self.assertEqual(pivot["Device 1"]["bgp"], "False")

    def test_cell_na(self):
        """None compliance (N/A) → "None" in pivot cell."""
        cc = self._create(self.dev1, self.feat_bgp, True)
        self._mark_na(cc)
        pivot = self._get_pivot()
        self.assertEqual(pivot["Device 1"]["bgp"], "None")

    def test_cell_no_record(self):
        """No ConfigCompliance record → device not in pivot at all."""
        pivot = self._get_pivot()
        self.assertNotIn("Device 1", pivot)

    # --- Per-device row ---

    def test_row_all_compliant(self):
        """Device with all features compliant → all cells are "True"."""
        self._create(self.dev1, self.feat_bgp, True)
        self._create(self.dev1, self.feat_ntp, True)
        self._create(self.dev1, self.feat_snmp, True)
        pivot = self._get_pivot()
        row = pivot["Device 1"]
        self.assertEqual(row["bgp"], "True")
        self.assertEqual(row["ntp"], "True")
        self.assertEqual(row["snmp"], "True")

    def test_row_all_non_compliant(self):
        """Device with all features non-compliant → all cells are "False"."""
        self._create(self.dev1, self.feat_bgp, False)
        self._create(self.dev1, self.feat_ntp, False)
        self._create(self.dev1, self.feat_snmp, False)
        pivot = self._get_pivot()
        row = pivot["Device 1"]
        self.assertEqual(row["bgp"], "False")
        self.assertEqual(row["ntp"], "False")
        self.assertEqual(row["snmp"], "False")

    def test_row_mixed_compliance(self):
        """Device with mixed compliance → cells are "True" and "False" accordingly."""
        self._create(self.dev1, self.feat_bgp, True)
        self._create(self.dev1, self.feat_ntp, False)
        self._create(self.dev1, self.feat_snmp, True)
        pivot = self._get_pivot()
        row = pivot["Device 1"]
        self.assertEqual(row["bgp"], "True")
        self.assertEqual(row["ntp"], "False")
        self.assertEqual(row["snmp"], "True")

    def test_row_all_na(self):
        """Device with all N/A records → device in pivot with all "None" cells."""
        cc1 = self._create(self.dev1, self.feat_bgp, True)
        cc2 = self._create(self.dev1, self.feat_ntp, True)
        cc3 = self._create(self.dev1, self.feat_snmp, True)
        self._mark_na(cc1)
        self._mark_na(cc2)
        self._mark_na(cc3)
        pivot = self._get_pivot()
        row = pivot["Device 1"]
        self.assertEqual(row["bgp"], "None")
        self.assertEqual(row["ntp"], "None")
        self.assertEqual(row["snmp"], "None")

    def test_row_mix_real_and_na(self):
        """Device with some real compliance and some N/A → N/A cells are "None", real cells are "True"/"False"."""
        self._create(self.dev1, self.feat_bgp, True)
        cc_na = self._create(self.dev1, self.feat_ntp, True)
        self._mark_na(cc_na)
        self._create(self.dev1, self.feat_snmp, False)
        pivot = self._get_pivot()
        row = pivot["Device 1"]
        self.assertEqual(row["bgp"], "True")
        self.assertEqual(row["ntp"], "None")
        self.assertEqual(row["snmp"], "False")

    def test_row_no_records_excluded(self):
        """Device with zero compliance records → not in pivot."""
        # Create records for another device so the pivot isn't empty
        self._create(self.dev4, self.feat_bgp, True)
        pivot = self._get_pivot()
        self.assertNotIn("Device 1", pivot)
        self.assertIn("Device 4", pivot)

    def test_row_partial_records(self):
        """Device with records for some features but not others → missing features are None (no record)."""
        self._create(self.dev1, self.feat_bgp, True)
        # No record for ntp or snmp
        pivot = self._get_pivot()
        row = pivot["Device 1"]
        self.assertEqual(row["bgp"], "True")
        self.assertIsNone(row.get("ntp"))
        self.assertIsNone(row.get("snmp"))

    def test_row_na_plus_no_record(self):
        """Device with only N/A records (no other features) → in pivot with "None" cells."""
        cc_na = self._create(self.dev1, self.feat_bgp, True)
        self._mark_na(cc_na)
        # No records for ntp or snmp
        pivot = self._get_pivot()
        row = pivot["Device 1"]
        self.assertEqual(row["bgp"], "None")

    def test_row_real_na_and_no_record(self):
        """Device with one real, one N/A, one missing → real is "True"/"False", N/A is "None", missing is None."""
        self._create(self.dev1, self.feat_bgp, False)
        cc_na = self._create(self.dev1, self.feat_ntp, True)
        self._mark_na(cc_na)
        # No record for snmp
        pivot = self._get_pivot()
        row = pivot["Device 1"]
        self.assertEqual(row["bgp"], "False")
        self.assertEqual(row["ntp"], "None")
        self.assertIsNone(row.get("snmp"))

    # --- Global scenarios ---

    def test_global_all_na(self):
        """When all compliance records across all devices are N/A, devices still appear with "None" cells."""
        cc1 = self._create(self.dev1, self.feat_bgp, True)
        cc2 = self._create(self.dev4, self.feat_ntp, True)
        self._mark_na(cc1)
        self._mark_na(cc2)
        pivot = self._get_pivot()
        self.assertIn("Device 1", pivot)
        self.assertEqual(pivot["Device 1"]["bgp"], "None")
        self.assertIn("Device 4", pivot)
        self.assertEqual(pivot["Device 4"]["ntp"], "None")

    def test_global_no_records_empty_pivot(self):
        """When no compliance records exist, pivot is empty."""
        pivot = self._get_pivot()
        self.assertEqual(len(pivot), 0)

    def test_global_mixed_devices(self):
        """Multiple devices with varying states all render correctly."""
        # dev1: all compliant
        self._create(self.dev1, self.feat_bgp, True)
        self._create(self.dev1, self.feat_ntp, True)
        # dev4: mixed
        self._create(self.dev4, self.feat_bgp, False)
        self._create(self.dev4, self.feat_ntp, True)
        # dev5: all N/A
        cc_na = self._create(self.dev5, self.feat_bgp, True)
        self._mark_na(cc_na)

        pivot = self._get_pivot()
        self.assertIn("Device 1", pivot)
        self.assertIn("Device 4", pivot)
        self.assertIn("Device 5", pivot)
        self.assertEqual(pivot["Device 5"]["bgp"], "None")
        self.assertEqual(pivot["Device 1"]["bgp"], "True")
        self.assertEqual(pivot["Device 1"]["ntp"], "True")
        self.assertEqual(pivot["Device 4"]["bgp"], "False")
        self.assertEqual(pivot["Device 4"]["ntp"], "True")


@override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
class FilteredComplianceDeviceIdsTestCase(TestCase):
    """Unit tests for views._get_filtered_compliance_device_ids.

    Covers the extraction of device IDs through ConfigComplianceFilterSet, including the
    regression case where filtering by multiple criteria (e.g. location + status) must not
    inflate annotation counts via Cartesian product row multiplication.
    """

    @classmethod
    def setUpTestData(cls):
        create_device_data()
        cls.dev1 = Device.objects.get(name="Device 1")
        cls.dev2 = Device.objects.get(name="Device 2")
        cls.dev4 = Device.objects.get(name="Device 4")
        # Assert the properties our filter tests depend on.  These are hardcoded in
        # create_device_data(); if that fixture ever changes these will fail loudly
        # rather than silently producing wrong test results.
        assert cls.dev1.status.name == "Active", "fixture assumption violated: Device 1 must be Active"
        assert cls.dev2.status.name == "Staged", "fixture assumption violated: Device 2 must be Staged"
        assert cls.dev4.status.name == "Active", "fixture assumption violated: Device 4 must be Active"
        assert (
            cls.dev1.platform == cls.dev4.platform
        ), "fixture assumption violated: Device 1 and 4 must share a platform"
        assert (
            cls.dev1.platform != cls.dev2.platform
        ), "fixture assumption violated: Device 1 and 2 must have different platforms"
        cls.rule_p1 = create_feature_rule_json(cls.dev1, feature="filt-feat-a")
        cls.rule_p2 = create_feature_rule_json(cls.dev2, feature="filt-feat-b")

    def _create_compliance(self, device, rule, compliant):
        actual = {"foo": "bar"}
        intended = {"foo": "bar"} if compliant else {"foo": "baz"}
        return models.ConfigCompliance.objects.create(device=device, rule=rule, actual=actual, intended=intended)

    def test_no_params_returns_all_devices_with_records(self):
        """Passing an empty dict returns every device that has a ConfigCompliance record."""
        self._create_compliance(self.dev1, self.rule_p1, 1)
        self._create_compliance(self.dev4, self.rule_p1, 0)
        device_ids = views._get_filtered_compliance_device_ids({})
        self.assertIn(self.dev1.id, device_ids)
        self.assertIn(self.dev4.id, device_ids)
        self.assertNotIn(self.dev2.id, device_ids)

    def test_single_criterion_filters_by_status(self):
        """A single status filter returns only devices with that status."""
        self._create_compliance(self.dev1, self.rule_p1, 1)  # Active
        self._create_compliance(self.dev2, self.rule_p2, 1)  # Staged
        device_ids = views._get_filtered_compliance_device_ids({"device_status": [self.dev1.status.name]})
        self.assertIn(self.dev1.id, device_ids)
        self.assertNotIn(self.dev2.id, device_ids)

    def test_multi_criteria_returns_intersection(self):
        """Filtering by platform AND status returns only devices matching both."""
        self._create_compliance(self.dev1, self.rule_p1, 1)  # Platform 1, Active  → included
        self._create_compliance(self.dev2, self.rule_p2, 1)  # Platform 2, Staged  → excluded
        device_ids = views._get_filtered_compliance_device_ids(
            {"platform": [str(self.dev1.platform.id)], "device_status": [self.dev1.status.name]}
        )
        self.assertIn(self.dev1.id, device_ids)
        self.assertNotIn(self.dev2.id, device_ids)

    def test_multi_criteria_deduplicates_device_ids(self):
        """A device with multiple compliance records appears exactly once (regression for missing .distinct()).

        Without .distinct(), a device with N compliance records matching the filter would
        produce N copies of its device_id in the flat values list.
        """
        # Give dev1 a second compliance record via a second feature on the same platform.
        rule_extra = create_feature_rule_json(self.dev1, feature="filt-feat-extra")
        self._create_compliance(self.dev1, self.rule_p1, 1)
        self._create_compliance(self.dev1, rule_extra, 1)  # second record for same device

        device_ids = views._get_filtered_compliance_device_ids(
            {"platform": [str(self.dev1.platform.id)], "device_status": [self.dev1.status.name]}
        )
        self.assertEqual(device_ids.count(self.dev1.id), 1, "dev1 must appear exactly once")
        self.assertEqual(len(device_ids), len(set(device_ids)), "no duplicates in result")

    def test_multi_criteria_annotation_counts_not_inflated(self):
        """Annotation counts are correct when device IDs come from a multi-criteria filter.

        Regression: if the filterset were applied directly to the annotated queryset instead
        of extracting device IDs first, multiple JOIN paths (platform join + status join)
        could multiply rows before aggregation, doubling count/compliant/non_compliant.
        """
        self._create_compliance(self.dev1, self.rule_p1, 1)  # compliant
        self._create_compliance(self.dev4, self.rule_p1, 0)  # non-compliant; same platform, same feature rule

        device_ids = views._get_filtered_compliance_device_ids(
            {"platform": [str(self.dev1.platform.id)], "device_status": [self.dev1.status.name]}
        )
        result = views._get_feature_compliance_queryset(device_ids).get(slug="filt-feat-a")
        # Would be 4/2/2 instead of 2/1/1 if Cartesian product doubled the rows.
        self.assertEqual(result.count, 2)
        self.assertEqual(result.compliant, 1)
        self.assertEqual(result.non_compliant, 1)
        self.assertAlmostEqual(result.comp_percent, 50.0)

    def test_non_matching_filter_returns_empty_list(self):
        """When no compliance records match all criteria the result is an empty list."""
        self._create_compliance(self.dev1, self.rule_p1, 1)  # Platform 1, Active
        # Filter: Platform 2 AND Active — dev2 is Platform 2 but Staged, so nothing matches.
        device_ids = views._get_filtered_compliance_device_ids(
            {"platform": [str(self.dev2.platform.id)], "device_status": [self.dev1.status.name]}
        )
        self.assertEqual(device_ids, [])

    def test_cartesian_product_naive_m2m_filter_inflates_count(self):
        """Ensure that filtering by multiple criteria does not inflate counts via Cartesian product row multiplication."""
        self._create_compliance(self.dev1, self.rule_p1, 1)
        self._create_compliance(self.dev4, self.rule_p1, 1)

        self.dev4.location = self.dev2.location  # we want same role but different location
        self.dev4.role = self.dev1.role
        self.dev4.save()

        query_params = {"role": [str(self.dev1.role.name)], "location_id": [str(self.dev1.location.id)]}
        filtered_device_ids = views._get_filtered_compliance_device_ids(query_params)

        result = views._get_feature_compliance_queryset(filtered_device_ids).get(slug="filt-feat-a")

        self.assertEqual(result.count, 1)  # If this fails, the Cartesian product regression is present
