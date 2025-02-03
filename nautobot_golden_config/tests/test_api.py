"""Unit tests for nautobot_golden_config."""

import tempfile
from copy import deepcopy
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.test import override_settings
from django.urls import reverse
from nautobot.apps.testing import APITestCase, APIViewTestCases
from nautobot.dcim.models import Device, Platform
from nautobot.extras.models import DynamicGroup, GitRepository, GraphQLQuery, Status
from packaging import version
from rest_framework import status

from nautobot_golden_config.choices import RemediationTypeChoice
from nautobot_golden_config.models import ConfigPlan, ConfigReplace, GoldenConfigSetting, RemediationSetting
from nautobot_golden_config.tests.conftest import (
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
            "backup_path_template": "{{obj.location.parent.name}}/{{obj.location.name}}/{{obj.name}}.cfg",
            "intended_path_template": "{{obj.location.parent.name}}/{{obj.location.name}}/{{obj.name}}.cfg",
            "jinja_path_template": "templates/{{obj.platform.name}}/{{obj.platform.name}}_main.j2",
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
            response.data["backup_path_template"], "{{obj.location.parent.name}}/{{obj.location.name}}/{{obj.name}}.cfg"
        )
        self.assertEqual(
            response.data["intended_path_template"],
            "{{obj.location.parent.name}}/{{obj.location.name}}/{{obj.name}}.cfg",
        )
        self.assertEqual(
            response.data["jinja_path_template"], "templates/{{obj.platform.name}}/{{obj.platform.name}}_main.j2"
        )
        self.assertFalse(response.data["backup_test_connectivity"])
        self.assertEqual(response.data["sot_agg_query"]["id"], GraphQLQuery.objects.get(name="GC-SoTAgg-Query-1").id)
        self.assertEqual(
            response.data["jinja_repository"]["id"], GitRepository.objects.get(name="test-jinja-repo-1").id
        )
        self.assertEqual(
            response.data["backup_repository"]["id"], GitRepository.objects.get(name="test-backup-repo-1").id
        )
        self.assertEqual(
            response.data["intended_repository"]["id"], GitRepository.objects.get(name="test-intended-repo-1").id
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
            response.data["backup_path_template"], "{{obj.location.parent.name}}/{{obj.location.name}}/{{obj.name}}.cfg"
        )
        self.assertEqual(
            response.data["intended_path_template"],
            "{{obj.location.parent.name}}/{{obj.location.name}}/{{obj.name}}.cfg",
        )
        self.assertEqual(
            response.data["jinja_path_template"], "templates/{{obj.platform.name}}/{{obj.platform.name}}_main.j2"
        )
        self.assertFalse(response.data["backup_test_connectivity"])
        self.assertEqual(response.data["sot_agg_query"]["id"], GraphQLQuery.objects.get(name="GC-SoTAgg-Query-1").id)
        self.assertEqual(
            response.data["jinja_repository"]["id"], GitRepository.objects.get(name="test-jinja-repo-1").id
        )
        self.assertEqual(
            response.data["backup_repository"]["id"], GitRepository.objects.get(name="test-backup-repo-1").id
        )
        self.assertEqual(
            response.data["intended_repository"]["id"], GitRepository.objects.get(name="test-intended-repo-1").id
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
        global_settings = GoldenConfigSetting.objects.create(dynamic_group=self.dynamic_group)
        global_settings.save()


# pylint: disable=too-many-ancestors


class GoldenConfigSerializerCSVTest(APITestCase):
    """Test CSV Export returns 200/OK."""

    url = reverse("plugins-api:nautobot_golden_config-api:goldenconfig-list")

    def setUp(self):
        super().setUp()
        self._add_permissions()

    def _add_permissions(self):
        model = self.url.split("/")[-2]
        permission_name = model.replace("-", "")
        self.add_permissions(f"nautobot_golden_config.view_{permission_name}")

    def test_csv_export(self):
        response = self.client.get(f"{self.url}?format=csv", **self.header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class GoldenConfigSettingSerializerCSVTest(GoldenConfigSerializerCSVTest):
    """Test CSV Export returns 200/OK."""

    url = reverse("plugins-api:nautobot_golden_config-api:goldenconfigsetting-list")

    def _add_permissions(self):
        self.add_permissions("nautobot_golden_config.view_goldenconfigsetting")


class ComplianceFeatureSerializerCSVTest(GoldenConfigSerializerCSVTest):
    """Test CSV Export returns 200/OK."""

    url = reverse("plugins-api:nautobot_golden_config-api:compliancefeature-list")


class ComplianceRuleCSVTest(GoldenConfigSerializerCSVTest):
    """Test CSV Export returns 200/OK."""

    url = reverse("plugins-api:nautobot_golden_config-api:compliancerule-list")


class ConfigComplianceCSVTest(GoldenConfigSerializerCSVTest):
    """Test CSV Export returns 200/OK."""

    url = reverse("plugins-api:nautobot_golden_config-api:configcompliance-list")


class ConfigRemoveCSVTest(GoldenConfigSerializerCSVTest):
    """Test CSV Export returns 200/OK."""

    url = reverse("plugins-api:nautobot_golden_config-api:configremove-list")


class ConfigReplaceCSVTest(GoldenConfigSerializerCSVTest):
    """Test CSV Export returns 200/OK."""

    url = reverse("plugins-api:nautobot_golden_config-api:configreplace-list")


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
            Platform.objects.create(name="Platform 4"),
            Platform.objects.create(name="Platform 5"),
            Platform.objects.create(name="Platform 6"),
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
class ConfigPlanTest(
    APIViewTestCases.GetObjectViewTestCase,
    APIViewTestCases.ListObjectsViewTestCase,
    APIViewTestCases.UpdateObjectViewTestCase,
    APIViewTestCases.DeleteObjectViewTestCase,
    APIViewTestCases.NotesURLViewTestCase,
):
    """Test API for ConfigPlan."""

    model = ConfigPlan
    brief_fields = ["device", "display", "id", "plan_type", "url"]

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
        not_approved_status = Status.objects.get(name="Not Approved")
        approved_status = Status.objects.get(name="Approved")

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
            "status": approved_status.pk,
        }

        cls.bulk_update_data = {
            "change_control_id": "Test Change Control ID 5",
            "change_control_url": "https://5.example.com/",
            "status": approved_status.pk,
        }

        # Account for test_options_returns_expected_choices behavior change for read_only choices fields
        if version.parse(settings.VERSION) < version.parse("2.4.0"):
            cls.choices_fields = ["plan_type"]


class ConfigReplaceAPITestCase(  # pylint: disable=too-many-ancestors
    APIViewTestCases.CreateObjectViewTestCase,
    APIViewTestCases.GetObjectViewTestCase,
    APIViewTestCases.ListObjectsViewTestCase,
    APIViewTestCases.UpdateObjectViewTestCase,
    APIViewTestCases.DeleteObjectViewTestCase,
    APIViewTestCases.NotesURLViewTestCase,
):
    """Test API for ConfigReplace."""

    model = ConfigReplace

    @classmethod
    def setUpTestData(cls):
        create_device_data()
        platform = Device.objects.first().platform
        for num in range(3):
            ConfigReplace.objects.create(
                name=f"test configreplace {num}",
                platform=platform,
                description="test description",
                regex="^(.*)$",
                replace="xyz",
            )
        cls.update_data = {
            "name": "new name",
            "platform": platform.pk,
            "description": "new description",
            "regex": "^NEW (.*)$",
            "replace": "NEW replaced text",
        }
        cls.create_data = [
            {
                "name": "test configreplace 4",
                "platform": platform.pk,
                "description": "test description",
                "regex": "^(.*)$",
                "replace": "xyz",
            },
            {
                "name": "test configreplace 5",
                "platform": platform.pk,
                "description": "test description",
                "regex": "^(.*)$",
                "replace": "xyz",
            },
            {
                "name": "test configreplace 6",
                "platform": platform.pk,
                "description": "test description",
                "regex": "^(.*)$",
                "replace": "xyz",
            },
        ]
        cls.bulk_update_data = {
            "description": "new description",
        }


class GenerateIntendedConfigViewAPITestCase(APITestCase):
    """Test API for GenerateIntendedConfigView."""

    @classmethod
    def setUpTestData(cls):
        # Delete the automatically created GoldenConfigSetting object
        GoldenConfigSetting.objects.all().delete()
        create_device_data()
        create_git_repos()
        create_saved_queries()

        cls.dynamic_group = DynamicGroup.objects.create(
            name="all devices dg",
            content_type=ContentType.objects.get_for_model(Device),
        )

        cls.device = Device.objects.get(name="Device 1")
        platform = cls.device.platform
        platform.network_driver = "arista_eos"
        platform.save()

        cls.git_repository = GitRepository.objects.get(name="test-jinja-repo-1")
        cls.golden_config_setting = GoldenConfigSetting.objects.create(
            name="GoldenConfigSetting test api generate intended config",
            slug="goldenconfigsetting-test-api-generate-intended-config",
            sot_agg_query=GraphQLQuery.objects.get(name="GC-SoTAgg-Query-2"),
            dynamic_group=cls.dynamic_group,
            jinja_repository=cls.git_repository,
            jinja_path_template="test.j2",
        )

    def _setup_mock_path(self, MockPath):  # pylint: disable=invalid-name
        mock_path_instance = MockPath.return_value
        mock_path_instance.__str__.return_value = "test.j2"
        mock_path_instance.is_file.return_value = True
        mock_path_instance.__truediv__.return_value = mock_path_instance  # to handle Path('path') / 'file'
        return mock_path_instance

    def _setup_mock_dispatcher(self, mock_dispatcher, template_file_callable=None):
        # Replicate nornir nested task structure
        def _mock_dispatcher(task, *args, **kwargs):
            def _template_file(*args, **kwargs):
                if template_file_callable:
                    return template_file_callable(*args, **kwargs)
                return None

            def _generate_config(task, *args, **kwargs):
                task.run(task=_template_file, name="template_file")
                return {"config": f"Jinja test for device {self.device.name}."}

            task.run(task=_generate_config, name="generate_config")
            return ""

        mock_dispatcher.side_effect = _mock_dispatcher

    @override_settings(VERSION="2.4.2")
    @patch("nautobot.extras.models.datasources.GitRepository.clone_to_directory_context", create=True)
    @patch("nautobot_golden_config.api.views.ensure_git_repository")
    @patch("nautobot_golden_config.api.views.Path")
    @patch("nautobot_golden_config.api.views.dispatcher")
    def test_generate_intended_config_branch_param_supported(
        self, mock_dispatcher, MockPath, mock_ensure_git_repository, mock_clone_to_directory_context
    ):  # pylint: disable=invalid-name
        """Verify that the intended config API succeeds when the branch parameter is supplied on Nautobot v2.4.2."""

        self.add_permissions("dcim.view_device")
        self.add_permissions("extras.view_gitrepository")

        self._setup_mock_path(MockPath)
        self._setup_mock_dispatcher(mock_dispatcher)

        with tempfile.TemporaryDirectory() as tmpdirname:
            mock_clone_to_directory_context.return_value.__enter__.return_value = tmpdirname
            response = self.client.get(
                reverse("plugins-api:nautobot_golden_config-api:generate_intended_config"),
                data={"device_id": self.device.pk, "branch": "main"},
                **self.header,
            )

        mock_clone_to_directory_context.assert_called_once()
        mock_ensure_git_repository.assert_called_once_with(self.git_repository)
        self.assertHttpStatus(response, status.HTTP_200_OK)
        self.assertTrue("intended_config" in response.data)
        self.assertTrue("intended_config_lines" in response.data)
        self.assertEqual(response.data["intended_config"], f"Jinja test for device {self.device.name}.")
        self.assertEqual(response.data["intended_config_lines"], [f"Jinja test for device {self.device.name}."])

    @override_settings(VERSION="2.4.1")
    @patch("nautobot_golden_config.api.views.ensure_git_repository")
    @patch("nautobot_golden_config.api.views.Path")
    @patch("nautobot_golden_config.api.views.dispatcher")
    def test_generate_intended_config_branch_param_unsupported(self, mock_dispatcher, MockPath, _):  # pylint: disable=invalid-name
        """Verify that the intended config API fails when the branch parameter is supplied on Nautobot <v2.4.2."""

        self.add_permissions("dcim.view_device")
        self.add_permissions("extras.view_gitrepository")

        self._setup_mock_path(MockPath)
        self._setup_mock_dispatcher(mock_dispatcher)

        response = self.client.get(
            reverse("plugins-api:nautobot_golden_config-api:generate_intended_config"),
            data={"device_id": self.device.pk, "branch": "main"},
            **self.header,
        )

        self.assertHttpStatus(response, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("detail" in response.data)
        self.assertEqual(
            response.data["detail"],
            "Branch support requires Nautobot v2.4.2 or later",
        )

    @patch("nautobot_golden_config.api.views.ensure_git_repository")
    @patch("nautobot_golden_config.api.views.Path")
    @patch("nautobot_golden_config.api.views.dispatcher")
    def test_generate_intended_config(self, mock_dispatcher, MockPath, mock_ensure_git_repository):  # pylint: disable=invalid-name
        """Verify that the intended config is generated as expected."""

        self.add_permissions("dcim.view_device")
        self.add_permissions("extras.view_gitrepository")

        self._setup_mock_path(MockPath)
        self._setup_mock_dispatcher(mock_dispatcher)

        response = self.client.get(
            reverse("plugins-api:nautobot_golden_config-api:generate_intended_config"),
            data={"device_id": self.device.pk},
            **self.header,
        )

        mock_ensure_git_repository.assert_called_once_with(self.git_repository)
        self.assertHttpStatus(response, status.HTTP_200_OK)
        self.assertTrue("intended_config" in response.data)
        self.assertTrue("intended_config_lines" in response.data)
        self.assertEqual(response.data["intended_config"], f"Jinja test for device {self.device.name}.")
        self.assertEqual(response.data["intended_config_lines"], [f"Jinja test for device {self.device.name}."])

    @patch("nautobot_golden_config.api.views.graph_ql_query")
    @patch("nautobot_golden_config.api.views.ensure_git_repository")
    @patch("nautobot_golden_config.api.views.Path")
    @patch("nautobot_golden_config.api.views.dispatcher")
    def test_generate_intended_config_graphql_query_id_param(self, mock_dispatcher, MockPath, _, mock_graph_ql_query):  # pylint: disable=invalid-name
        """Verify that the intended config is generated as expected."""

        self.add_permissions("dcim.view_device")
        self.add_permissions("extras.view_gitrepository")

        self._setup_mock_path(MockPath)
        self._setup_mock_dispatcher(mock_dispatcher)

        self.client.get(
            reverse("plugins-api:nautobot_golden_config-api:generate_intended_config"),
            data={
                "device_id": self.device.pk,
                "graphql_query_id": GraphQLQuery.objects.get(name="GC-SoTAgg-Query-1").id,
            },
            **self.header,
        )

        self.assertEqual(len(mock_graph_ql_query.call_args.args), 3)
        self.assertEqual(
            mock_graph_ql_query.call_args.args[2], GraphQLQuery.objects.get(name="GC-SoTAgg-Query-1").query
        )

        mock_graph_ql_query.reset_mock()
        self.client.get(
            reverse("plugins-api:nautobot_golden_config-api:generate_intended_config"),
            data={
                "device_id": self.device.pk,
                "graphql_query_id": GraphQLQuery.objects.get(name="GC-SoTAgg-Query-2").id,
            },
            **self.header,
        )

        self.assertEqual(len(mock_graph_ql_query.call_args.args), 3)
        self.assertEqual(
            mock_graph_ql_query.call_args.args[2], GraphQLQuery.objects.get(name="GC-SoTAgg-Query-2").query
        )

    @patch("nautobot_golden_config.api.views.ensure_git_repository")
    @patch("nautobot_golden_config.api.views.Path")
    @patch("nautobot_golden_config.api.views.dispatcher")
    def test_generate_intended_config_failures(self, mock_dispatcher, MockPath, mock_ensure_git_repository):  # pylint: disable=invalid-name
        """Verify that errors are handled as expected."""

        self.add_permissions("dcim.view_device")
        self.add_permissions("extras.view_gitrepository")

        mock_path_instance = self._setup_mock_path(MockPath)

        # test missing query parameters
        response = self.client.get(
            reverse("plugins-api:nautobot_golden_config-api:generate_intended_config"),
            data={},
            **self.header,
        )
        self.assertHttpStatus(response, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("detail" in response.data)
        self.assertEqual(
            response.data["detail"],
            "Parameter device_id is required",
        )

        # test git repo not present on filesystem
        mock_path_instance.is_file.return_value = False

        response = self.client.get(
            reverse("plugins-api:nautobot_golden_config-api:generate_intended_config"),
            data={"device_id": self.device.pk},
            **self.header,
        )

        self.assertHttpStatus(response, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("detail" in response.data)
        self.assertEqual(
            response.data["detail"],
            f"Error rendering Jinja template: Jinja template test.j2 not found in git repository {self.git_repository}",
        )

        # test exception raised in nornir task
        def _template_file_code(*args, **kwargs):
            raise Exception("Test exception")  # pylint: disable=broad-exception-raised

        self._setup_mock_dispatcher(mock_dispatcher, template_file_callable=_template_file_code)
        mock_path_instance.is_file.return_value = True

        response = self.client.get(
            reverse("plugins-api:nautobot_golden_config-api:generate_intended_config"),
            data={"device_id": self.device.pk},
            **self.header,
        )

        self.assertHttpStatus(response, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("detail" in response.data)
        self.assertEqual(
            response.data["detail"].strip(),
            "Error rendering Jinja template: Subtask: GENERATE CONFIG (failed)",
        )

        # test ensure_git_repository failure
        mock_ensure_git_repository.side_effect = Exception("Test exception")

        response = self.client.get(
            reverse("plugins-api:nautobot_golden_config-api:generate_intended_config"),
            data={"device_id": self.device.pk},
            **self.header,
        )

        self.assertHttpStatus(response, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("detail" in response.data)
        self.assertEqual("Error trying to sync git repository", response.data["detail"])

        # test no sot_agg_query on GoldenConfigSetting
        self.golden_config_setting.sot_agg_query = None
        self.golden_config_setting.save()

        response = self.client.get(
            reverse("plugins-api:nautobot_golden_config-api:generate_intended_config"),
            data={"device_id": self.device.pk},
            **self.header,
        )

        self.assertHttpStatus(response, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("detail" in response.data)
        self.assertEqual("Golden Config settings sot_agg_query not set", response.data["detail"])

        # test jinja_repository not set
        self.golden_config_setting.jinja_repository = None
        self.golden_config_setting.save()

        response = self.client.get(
            reverse("plugins-api:nautobot_golden_config-api:generate_intended_config"),
            data={"device_id": self.device.pk},
            **self.header,
        )

        self.assertHttpStatus(response, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("detail" in response.data)
        self.assertEqual(response.data["detail"], "Golden Config settings jinja_repository not set")

        # test no GoldenConfigSetting found for device
        GoldenConfigSetting.objects.all().delete()
        response = self.client.get(
            reverse("plugins-api:nautobot_golden_config-api:generate_intended_config"),
            data={"device_id": self.device.pk},
            **self.header,
        )

        self.assertHttpStatus(response, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("detail" in response.data)
        self.assertEqual("No Golden Config settings found for this device", response.data["detail"])
