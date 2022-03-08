"""Unit tests for nautobot_golden_config."""
from copy import deepcopy
from django.contrib.auth import get_user_model

from django.urls import reverse
from rest_framework import status

from nautobot.utilities.testing import APITestCase
from nautobot.extras.models import GitRepository, GraphQLQuery
from nautobot_golden_config.models import GoldenConfigSetting

from .conftest import (
    create_device,
    create_feature_rule_json,
    create_config_compliance,
    create_git_repos,
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


class GoldenConfigSettingsAPITest(APITestCase):
    """Verify that the combination of values in a GoldenConfigSettings object POST are valid."""

    def setUp(self):
        """Create a superuser and token for API calls."""
        super().setUp()
        create_git_repos()
        create_saved_queries()
        self.add_permissions("nautobot_golden_config.add_goldenconfigsetting")
        self.add_permissions("nautobot_golden_config.change_goldenconfigsetting")
        self.base_view = reverse("plugins-api:nautobot_golden_config-api:goldenconfigsetting-list")
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
            "scope": {"has_primary_ip": "True"},
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

    def test_settings_api_clean_up(self):
        """Transactional custom model, unable to use `get_or_create`.

        Delete all objects created of GitRepository type.
        """
        GitRepository.objects.all().delete()
        self.assertEqual(GitRepository.objects.all().count(), 0)

        # Put back a general GoldenConfigSetting object.
        global_settings = GoldenConfigSetting.objects.create()
        global_settings.save()
