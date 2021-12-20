"""Tests for Golden Configuration Settings Form."""

from django.test import TestCase
from nautobot.extras.models import GitRepository
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
                "backup_repository": [GitRepository.objects.get(name="test-backup-repo-1"), GitRepository.objects.get(name="test-backup-repo-2")],
                "backup_match_rule": "backup-{{ obj.site.region.parent.slug }}",
                "backup_path_template": "{{ obj.site.region.parent.slug }}/{{obj.name}}.cfg",
                "intended_repository": [GitRepository.objects.get(name="test-intended-repo-1"), GitRepository.objects.get(name="test-intended-repo-2")],
                "intended_match_rule": "intended-{{ obj.site.region.parent.slug }}",
                "intended_path_template": "{{ obj.site.slug }}/{{ obj.name }}.cfg",
                "backup_test_connectivity": True,
            }
        )
        self.assertTrue(form.is_valid())
        self.assertTrue(form.save())

    def test_clean_backup_template(self):
        """Testing clean method for single backup repo with a matching pattern."""
        form = GoldenConfigSettingFeatureForm(
            data={
                "backup_repository": [GitRepository.objects.get(name="test-backup-repo-2")],
                "backup_match_rule": "backup-{{ obj.site.region.parent.slug }}",
                "backup_path_template": "{{ obj.site.region.parent.slug }}/{{obj.name}}.cfg",
                "intended_repository": [GitRepository.objects.get(name="test-intended-repo-1"), GitRepository.objects.get(name="test-intended-repo-2")],
                "intended_match_rule": "intended-{{ obj.site.region.parent.slug }}",
                "intended_path_template": "{{ obj.site.slug }}/{{ obj.name }}.cfg",
                "backup_test_connectivity": True,
            }
        )
        self.assertFalse(form.is_valid())
        self.assertEqual(form.non_field_errors(), ["If you configure only one backup repository, there is no need to specify the backup repository matching rule template."])

    def test_clean_intended_template(self):
        """Testing clean method for single intended repo with a matching pattern."""
        form = GoldenConfigSettingFeatureForm(
            data={
                "backup_repository": [GitRepository.objects.get(name="test-backup-repo-2")],
                "backup_path_template": "{{ obj.site.region.parent.slug }}/{{obj.name}}.cfg",
                "intended_repository": [GitRepository.objects.get(name="test-intended-repo-1")],
                "intended_match_rule": "intended-{{ obj.site.region.parent.slug }}",
                "intended_path_template": "{{ obj.site.slug }}/{{ obj.name }}.cfg",
                "backup_test_connectivity": True,
            }
        )
        self.assertFalse(form.is_valid())
        self.assertEqual(form.non_field_errors(), ["If you configure only one intended repository, there is no need to specify the intended repository matching rule template."])

    def test_clean_up(self):
        """Transactional custom model, unable to use `get_or_create`.

        Delete all objects created of GitRepository type.
        """
        GitRepository.objects.all().delete()
        self.assertEqual(GitRepository.objects.all().count(), 0)

        # Put back a general GoldenConfigSetting object.
        global_settings = GoldenConfigSetting.objects.create()
        global_settings.save()
