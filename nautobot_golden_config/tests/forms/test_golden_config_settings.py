"""Tests for Golden Configuration Settings Form."""
from unittest import mock

from django.test import TestCase

from nautobot.extras.models import GitRepository, DynamicGroup
from nautobot_golden_config.forms import GoldenConfigSettingForm
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
        with mock.patch("nautobot_golden_config.models.ENABLE_SOTAGG", False):
            form = GoldenConfigSettingForm(
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

    def test_no_query_fail(self):
        """Testing GoldenConfigForm without specifying a unique scope or GraphQL Query."""
        with mock.patch("nautobot_golden_config.models.ENABLE_SOTAGG", True):
            form = GoldenConfigSettingForm(
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
            self.assertFalse(form.is_valid())
            self.assertEqual(form.errors["__all__"][0], "A GraphQL query must be defined when `ENABLE_SOTAGG` is True")

    def test_clean_up(self):
        """Transactional custom model, unable to use `get_or_create`.

        Delete all objects created of GitRepository type.
        """
        GitRepository.objects.all().delete()
        self.assertEqual(GitRepository.objects.all().count(), 0)
