"""Unit tests for nautobot_golden_config."""
from copy import deepcopy

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from nautobot.dcim.models import Device, Platform
from nautobot.extras.models import DynamicGroup, GitRepository, GraphQLQuery, Status
from nautobot.utilities.testing import APITestCase, APIViewTestCases
from rest_framework import status

from nautobot_golden_config.choices import RemediationTypeChoice
from nautobot_golden_config.models import ConfigPlan, GoldenConfigSetting, RemediationSetting

from .conftest import (
    create_config_compliance,
    create_device,
    create_device_data,
    create_feature_rule_json,
    create_git_repos,
    create_job_result,
    create_saved_queries,
)

User = get_user_model()


class GoldenConfigAPITest(APITestCase):  # pylint: disable=too-many-ancestors
    """Test the ConfigCompliance API."""

    def setUp(self):
        """Create a superuser and token for API calls."""
        super().setUp()
        self.device = create_device()
        self.compliance_rule_json = create_feature_rule_json(self.device)
        self.base_view = reverse("plugins-api:nautobot_golden_config-api:configcompliance-list")

    def test_root(self):
        """Validate the root for Nautobot Chatops API."""
        url = reverse("plugins-api:nautobot_golden_config-api:api-root")
        response = self.client.get(f"{url}?format=api", **self.header)
        self.assertEqual(response.status_code, 200)

    def test_device_list(self):
        """Verify that devices can be listed."""
        url = reverse("dcim-api:device-list")
        self.add_permissions("dcim.view_device")
        response = self.client.get(url, **self.header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    def test_config_compliance_list_view(self):
        """Verify that config compliance objects can be listed."""
        actual = '{"foo": {"bar-1": "baz"}}'
        intended = '{"foo": {"bar-2": "baz"}}'
        create_config_compliance(
            self.device, actual=actual, intended=intended, compliance_rule=self.compliance_rule_json
        )
        self.add_permissions("nautobot_golden_config.view_configcompliance")
        response = self.client.get(self.base_view, **self.header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    def test_config_compliance_post_new_json_compliant(self):
        """Verify that config compliance detail view."""
        self.add_permissions("nautobot_golden_config.add_configcompliance")
        response = self.client.post(
            self.base_view,
            data={
                "device": self.device.id,
                "intended": '{"foo": {"bar-1": "baz"}}',
                "actual": '{"foo": {"bar-1": "baz"}}',
                "rule": self.compliance_rule_json.id,
            },
            format="json",
            **self.header,
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["compliance"])

    def test_config_compliance_post_new_json_not_compliant(self):
        """Verify that config compliance detail view."""
        self.add_permissions("nautobot_golden_config.add_configcompliance")
        response = self.client.post(
            self.base_view,
            data={
                "device": self.device.id,
                "intended": '{"foo": {"bar-1": "baz"}}',
                "actual": '{"foo": {"bar-2": "baz"}}',
                "rule": self.compliance_rule_json.id,
            },
            format="json",
            **self.header,
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertFalse(response.data["compliance"])


class GoldenConfigSettingsAPITest(APITestCase):  # pylint: disable=too-many-ancestors
    """Verify that the combination of values in a GoldenConfigSettings object POST are valid."""

    def setUp(self):
        """Create a superuser and token for API calls."""
        super().setUp()
        create_git_repos()
        create_saved_queries()
        self.add_permissions("nautobot_golden_config.add_goldenconfigsetting")
        self.add_permissions("nautobot_golden_config.change_goldenconfigsetting")
        self.add_permissions("extras.view_dynamicgroup")
        self.base_view = reverse("plugins-api:nautobot_golden_config-api:goldenconfigsetting-list")
        self.content_type = ContentType.objects.get(app_label="dcim", model="device")
        self.dynamic_group = DynamicGroup.objects.create(
            name="test1 site site-4",
            slug="test1-site-site-4",
            content_type=self.content_type,
            filter={"has_primary_ip": "True"},
        )

        self.data = {
            "name": "test-setting-1",
            "slug": "test_setting_1",
            "description": "This is a description field of test-setting-1.",
            "weight": 5000,
            "tags": [],
            "computed_fields": {},
            "custom_fields": {},
            "_custom_field_data": {},
            "backup_path_template": "{{obj.site.region.slug}}/{{obj.site.slug}}/{{obj.name}}.cfg",
            "intended_path_template": "{{obj.site.region.slug}}/{{obj.site.slug}}/{{obj.name}}.cfg",
            "jinja_path_template": "templates/{{obj.platform.slug}}/{{obj.platform.slug}}_main.j2",
            "backup_test_connectivity": False,
            "dynamic_group": str(self.dynamic_group.id),
            "sot_agg_query": str(GraphQLQuery.objects.get(name="GC-SoTAgg-Query-1").id),
            "jinja_repository": str(GitRepository.objects.get(name="test-jinja-repo-1").id),
            "backup_repository": str(GitRepository.objects.get(name="test-backup-repo-1").id),
            "intended_repository": str(GitRepository.objects.get(name="test-intended-repo-1").id),
        }
        # Since we enforced a singleton pattern on this model in 0.9 release migrations, nuke any auto-created objects.
        GoldenConfigSetting.objects.all().delete()

    def test_golden_config_settings_create_good(self):
        """Test a POST with good values."""
        response = self.client.post(
            self.base_view,
            data=self.data,
            format="json",
            **self.header,
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["created"])
        self.assertTrue(response.data["id"])
        self.assertEqual(
            response.data["backup_path_template"], "{{obj.site.region.slug}}/{{obj.site.slug}}/{{obj.name}}.cfg"
        )
        self.assertEqual(
            response.data["intended_path_template"], "{{obj.site.region.slug}}/{{obj.site.slug}}/{{obj.name}}.cfg"
        )
        self.assertEqual(
            response.data["jinja_path_template"], "templates/{{obj.platform.slug}}/{{obj.platform.slug}}_main.j2"
        )
        self.assertFalse(response.data["backup_test_connectivity"])
        self.assertEqual(response.data["scope"], {"has_primary_ip": "True"})
        self.assertEqual(response.data["sot_agg_query"], GraphQLQuery.objects.get(name="GC-SoTAgg-Query-1").id)
        self.assertEqual(response.data["jinja_repository"], GitRepository.objects.get(name="test-jinja-repo-1").id)
        self.assertEqual(response.data["backup_repository"], GitRepository.objects.get(name="test-backup-repo-1").id)
        self.assertEqual(
            response.data["intended_repository"], GitRepository.objects.get(name="test-intended-repo-1").id
        )
        # Clean up
        GoldenConfigSetting.objects.all().delete()
        self.assertEqual(GoldenConfigSetting.objects.all().count(), 0)

    def test_golden_config_settings_update_good(self):
        """Verify a PUT to the valid settings object, with valid but changed values."""
        response_post = self.client.post(
            self.base_view,
            data=self.data,
            format="json",
            **self.header,
        )
        new_data = deepcopy(self.data)
        new_data["backup_repository"] = str(GitRepository.objects.get(name="test-backup-repo-1").id)
        response = self.client.put(
            f"{self.base_view}{response_post.data['id']}/",
            data=new_data,
            format="json",
            **self.header,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["backup_path_template"], "{{obj.site.region.slug}}/{{obj.site.slug}}/{{obj.name}}.cfg"
        )
        self.assertEqual(
            response.data["intended_path_template"], "{{obj.site.region.slug}}/{{obj.site.slug}}/{{obj.name}}.cfg"
        )
        self.assertEqual(
            response.data["jinja_path_template"], "templates/{{obj.platform.slug}}/{{obj.platform.slug}}_main.j2"
        )
        self.assertFalse(response.data["backup_test_connectivity"])
        self.assertEqual(response.data["scope"], {"has_primary_ip": "True"})
        self.assertEqual(response.data["sot_agg_query"], GraphQLQuery.objects.get(name="GC-SoTAgg-Query-1").id)
        self.assertEqual(response.data["jinja_repository"], GitRepository.objects.get(name="test-jinja-repo-1").id)
        self.assertEqual(response.data["backup_repository"], GitRepository.objects.get(name="test-backup-repo-1").id)
        self.assertEqual(
            response.data["intended_repository"], GitRepository.objects.get(name="test-intended-repo-1").id
        )
        # Clean up
        GoldenConfigSetting.objects.all().delete()
        self.assertEqual(GoldenConfigSetting.objects.all().count(), 0)

    def test_scope_and_dynamic_group_create(self):
        """Attempts to create object with both scope & dynamic group set."""
        new_data = deepcopy(self.data)
        new_data["scope"] = {"has_primary_ip": "True"}
        response = self.client.post(
            self.base_view,
            data=new_data,
            format="json",
            **self.header,
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json(),
            {"non_field_errors": ["Payload can only contain `scope` or `dynamic_group`, but both were provided."]},
        )

    def test_scope_create(self):
        """Attempts to create object with only scope."""
        new_data = deepcopy(self.data)
        new_data["scope"] = {"has_primary_ip": "True"}
        new_data.pop("dynamic_group")
        response = self.client.post(
            self.base_view,
            data=new_data,
            format="json",
            **self.header,
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()["dynamic_group"]["name"], f"GoldenConfigSetting {new_data['name']} scope")
        # Clean up
        GoldenConfigSetting.objects.all().delete()
        self.assertEqual(GoldenConfigSetting.objects.all().count(), 0)

    def test_golden_config_settings_update_scope(self):
        """Verify a PATCH to the valid settings object, with just scope."""
        response_post = self.client.post(
            self.base_view,
            data=self.data,
            format="json",
            **self.header,
        )
        response = self.client.patch(
            f"{self.base_view}{response_post.data['id']}/",
            data={"scope": {"has_primary_ip": "False"}},
            format="json",
            **self.header,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["scope"], {"has_primary_ip": "False"})
        dg_response = self.client.get(
            response.json()["dynamic_group"]["url"],
            format="json",
            **self.header,
        )
        self.assertEqual(dg_response.json()["filter"], {"has_primary_ip": "False"})
        # Clean up
        GoldenConfigSetting.objects.all().delete()
        self.assertEqual(GoldenConfigSetting.objects.all().count(), 0)

    def test_settings_api_clean_up(self):
        """Transactional custom model, unable to use `get_or_create`.

        Delete all objects created of GitRepository type.
        """
        GitRepository.objects.all().delete()
        self.assertEqual(GitRepository.objects.all().count(), 0)

        # Put back a general GoldenConfigSetting object.
        global_settings = GoldenConfigSetting.objects.create(dynamic_group=self.dynamic_group)
        global_settings.save()


# pylint: disable=too-many-ancestors
class RemediationSettingTest(APIViewTestCases.APIViewTestCase):
    """Test API for Remediation Settings."""

    model = RemediationSetting
    choices_fields = ["remediation_type"]

    @classmethod
    def setUpTestData(cls):
        create_device_data()
        platform1 = Platform.objects.get(name="Platform 1")
        platform2 = Platform.objects.get(name="Platform 2")
        platform3 = Platform.objects.get(name="Platform 3")
        type_cli = RemediationTypeChoice.TYPE_HIERCONFIG
        type_custom = RemediationTypeChoice.TYPE_CUSTOM

        # RemediationSetting type Hier with default values.
        RemediationSetting.objects.create(
            platform=platform1,
            remediation_type=type_cli,
        )
        # RemediationSetting type Hier with custom options.
        RemediationSetting.objects.create(
            platform=platform2, remediation_type=type_cli, remediation_options={"some_option": "some_value"}
        )
        # RemediationSetting type Custom with custom options.
        RemediationSetting.objects.create(
            platform=platform3,
            remediation_type=type_custom,
        )

        platforms = (
            Platform.objects.create(name="Platform 4", slug="platform-4"),
            Platform.objects.create(name="Platform 5", slug="platform-5"),
            Platform.objects.create(name="Platform 6", slug="platform-6"),
        )

        cls.create_data = [
            {"platform": platforms[0].pk, "remediation_type": type_cli},
            {
                "platform": platforms[1].pk,
                "remediation_type": type_cli,
                "remediation_options": {"some_option": "some_value"},
            },
            {"platform": platforms[2].pk, "remediation_type": type_custom},
        ]

        cls.update_data = {
            "remediation_type": type_custom,
        }

        cls.bulk_update_data = {
            "remediation_type": type_cli,
        }

    def test_list_objects_brief(self):
        """Skipping test due to brief_fields not implemented."""


# pylint: disable=too-many-ancestors,too-many-locals
class ConfigPlanTest(APIViewTestCases.APIViewTestCase):
    """Test API for ConfigPlan."""

    model = ConfigPlan
    brief_fields = ["device", "display", "id", "plan_type", "url"]
    # The Status serializer field requires slug, but the model field returns the UUID.
    validation_excluded_fields = ["status"]

    @classmethod
    def setUpTestData(cls):
        create_device_data()
        device1 = Device.objects.get(name="Device 1")
        device2 = Device.objects.get(name="Device 2")
        device3 = Device.objects.get(name="Device 3")

        rule1 = create_feature_rule_json(device1, feature="Test Feature 1")
        rule2 = create_feature_rule_json(device2, feature="Test Feature 2")
        rule3 = create_feature_rule_json(device3, feature="Test Feature 3")

        job_result1 = create_job_result()
        job_result2 = create_job_result()
        job_result3 = create_job_result()

        features = [rule1.feature, rule2.feature, rule3.feature]
        plan_types = ["intended", "missing", "remediation"]
        job_result_ids = [job_result1.id, job_result2.id, job_result3.id]
        not_approved_status = Status.objects.get(slug="not-approved")
        approved_status = Status.objects.get(slug="approved")

        for cont in range(1, 4):
            plan = ConfigPlan.objects.create(
                device=Device.objects.get(name=f"Device {cont}"),
                plan_type=plan_types[cont - 1],
                config_set=f"Test Config Set {cont}",
                change_control_id=f"Test Change Control ID {cont}",
                change_control_url=f"https://{cont}.example.com/",
                status=not_approved_status,
                plan_result_id=job_result_ids[cont - 1],
            )
            plan.feature.add(features[cont - 1])
            plan.validated_save()

        cls.update_data = {
            "change_control_id": "Test Change Control ID 4",
            "change_control_url": "https://4.example.com/",
            "status": approved_status.slug,
        }

        cls.bulk_update_data = {
            "change_control_id": "Test Change Control ID 5",
            "change_control_url": "https://5.example.com/",
            "status": approved_status.slug,
        }

    def test_create_object(self):
        """Skipping test due to POST method not allowed."""

    def test_create_object_without_permission(self):
        """Skipping test due to POST method not allowed."""

    def test_bulk_create_objects(self):
        """Skipping test due to POST method not allowed."""
