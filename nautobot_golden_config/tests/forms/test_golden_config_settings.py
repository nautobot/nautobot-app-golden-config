"""Tests for Golden Configuration Settings Form."""

from django.test import TestCase
from nautobot.extras.models import DynamicGroup, GitRepository, GraphQLQuery

from nautobot_golden_config.forms import GoldenConfigSettingForm
from nautobot_golden_config.models import GoldenConfigSetting
from nautobot_golden_config.tests.conftest import create_device_data, create_git_repos, create_saved_queries


class GoldenConfigSettingFormTest(TestCase):
    """Test Golden Config Setting Feature Form."""

    def setUp(self):
        """Setup test data."""
        create_git_repos()
        create_device_data()
        create_saved_queries()
        # Since we enforce a singleton pattern on this model, nuke the auto-created object.
        GoldenConfigSetting.objects.all().delete()
        self.gc_settings_data = {
            "name": "test",
            "slug": "test",
            "weight": 1000,
            "description": "Test description.",
            "backup_repository": str(GitRepository.objects.get(name="test-backup-repo-1").id),
            "backup_path_template": "{{ obj.location.name }}/{{obj.name}}.cfg",
            "intended_repository": str(GitRepository.objects.get(name="test-intended-repo-1").id),
            "intended_path_template": "{{ obj.location.name }}/{{ obj.name }}.cfg",
            "jinja_repository": str(GitRepository.objects.get(name="test-jinja-repo-1").id),
            "jinja_path_template": "{{ obj.platform.network_driver }}.j2",
            "backup_test_connectivity": True,
            "dynamic_group": DynamicGroup.objects.first(),
            "backup_enabled": True,
            "compliance_enabled": True,
            "plan_enabled": True,
            "deploy_enabled": True,
        }

    def test_no_query_no_scope_success(self):
        """Testing GoldenConfigSettingForm intended disabled no query success."""
        # NOTICE self.gc_settings_data["sot_agg_query"] is not in the form data.
        self.gc_settings_data["intended_enabled"] = False
        form = GoldenConfigSettingForm(data=self.gc_settings_data)
        self.assertTrue(form.is_valid())
        self.assertTrue(form.save())

    def test_intended_no_query_fail(self):
        """Testing GoldenConfigSettingForm intended enabled no query failure."""
        # NOTICE self.gc_settings_data["sot_agg_query"] is not in the form data.
        self.gc_settings_data["intended_enabled"] = True
        form = GoldenConfigSettingForm(data=self.gc_settings_data)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["__all__"][0], "A GraphQL query must be defined when Intended Enabled is checked.")

    def test_intended_with_sotagg_query_success(self):
        """Testing GoldenConfigSettingForm intended enabled query set success."""
        self.gc_settings_data["intended_enabled"] = True
        self.gc_settings_data["sot_agg_query"] = GraphQLQuery.objects.get(name="GC-SoTAgg-Query-1").id
        form = GoldenConfigSettingForm(data=self.gc_settings_data)
        self.assertTrue(form.is_valid())
        self.assertTrue(form.save())

    def test_intended_with_sotagg_invalid_query(self):
        """Testing GoldenConfigSettingForm invalid sotagg query."""
        self.gc_settings_data["intended_enabled"] = True
        self.gc_settings_data["sot_agg_query"] = GraphQLQuery.objects.get(name="GC-SoTAgg-Query-5").id
        form = GoldenConfigSettingForm(data=self.gc_settings_data)
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors["__all__"][0], "The GraphQL query must start with exactly `query ($device_id: ID!)`"
        )
