"""Tests for Golden Configuration Settings Form."""

from django.test import TestCase
from nautobot.extras.models import GitRepository, DynamicGroup
from nautobot_golden_config.forms import GoldenConfigSettingFeatureForm
from nautobot_golden_config.models import GoldenConfigSetting
from nautobot_golden_config.tests.conftest import create_git_repos, create_device_data


class GoldenConfigSettingFormTest(TestCase):
    """Test Golden Config Setting Feature Form."""

    def setUp(self) -> None:
        """Setup test data."""
        create_git_repos()
        create_device_data()
        # Since we enforce a singleton pattern on this model, nuke the auto-created object.
        GoldenConfigSetting.objects.all().delete()

    def test_no_query_no_scope_success(self):
        """Testing GoldenConfigForm without specifying a unique scope or GraphQL Query."""
        form = GoldenConfigSettingFeatureForm(
            data={
                "name": "test",
                "slug": "test",
                "weight": 1000,
                "description": "Test description.",
                "backup_repository": GitRepository.objects.get(name="test-backup-repo-1"),
                "backup_path_template": "{{ obj.site.region.parent.slug }}/{{obj.name}}.cfg",
                "intended_repository": GitRepository.objects.get(name="test-intended-repo-1"),
                "intended_path_template": "{{ obj.site.slug }}/{{ obj.name }}.cfg",
                "backup_test_connectivity": True,
                "dynamic_group": DynamicGroup.objects.first()
            }
        )
        self.assertTrue(form.is_valid())
        self.assertTrue(form.save())

    def test_clean_up(self):
        """Transactional custom model, unable to use `get_or_create`.

        Delete all objects created of GitRepository type.
        """
        GitRepository.objects.all().delete()
        self.assertEqual(GitRepository.objects.all().count(), 0)
