"""Tests for Golden Configuration Settings Form."""

from django.contrib.contenttypes.models import ContentType
from nautobot.apps.testing import TestCase
from nautobot.dcim.models import Device
from nautobot.extras.models import DynamicGroup, GitRepository

from nautobot_golden_config.forms import GoldenConfigSettingForm
from nautobot_golden_config.models import GoldenConfigSetting
from nautobot_golden_config.tests.conftest import create_device_data, create_git_repos


class GoldenConfigSettingFormTest(TestCase):
    """Test Golden Config Setting Feature Form."""

    @classmethod
    def setUpTestData(cls) -> None:
        """Setup test data."""
        create_git_repos()
        create_device_data()
        # Since we enforce a singleton pattern on this model, nuke the auto-created object.
        GoldenConfigSetting.objects.all().delete()

    def test_intended_disabled_no_query_success(self):
        """With ``enable_intended=False`` the form must accept a Setting without ``sot_agg_query``."""
        dynamic_group = DynamicGroup.objects.create(
            name="GoldenConfig Default Group",
            filter={},
            content_type=ContentType.objects.get_for_model(Device),
        )
        form = GoldenConfigSettingForm(
            data={
                "name": "test",
                "slug": "test",
                "weight": 1000,
                "description": "Test description.",
                "backup_repository": GitRepository.objects.get(name="test-backup-repo-1"),
                "backup_path_template": "{{ obj.location.name }}/{{obj.name}}.cfg",
                "intended_repository": GitRepository.objects.get(name="test-intended-repo-1"),
                "intended_path_template": "{{ obj.location.name }}/{{ obj.name }}.cfg",
                "backup_test_connectivity": True,
                "dynamic_group": dynamic_group.pk,
                "enable_backup": True,
                "enable_intended": False,
                "enable_compliance": True,
                "enable_plan": True,
                "enable_deploy": True,
            }
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertTrue(form.save())

    def test_intended_enabled_without_required_fields_fail(self):
        """With ``enable_intended=True`` the form must reject a Setting missing ``sot_agg_query``."""
        dynamic_group = DynamicGroup.objects.create(
            name="GoldenConfig Default Group",
            filter={},
            content_type=ContentType.objects.get_for_model(Device),
        )
        form = GoldenConfigSettingForm(
            data={
                "name": "test",
                "slug": "test",
                "weight": 1000,
                "description": "Test description.",
                "backup_repository": GitRepository.objects.get(name="test-backup-repo-1"),
                "backup_path_template": "{{ obj.location.name }}/{{obj.name}}.cfg",
                "intended_repository": GitRepository.objects.get(name="test-intended-repo-1"),
                "intended_path_template": "{{ obj.location.name }}/{{ obj.name }}.cfg",
                "jinja_repository": GitRepository.objects.get(name="test-jinja-repo-1"),
                "jinja_path_template": "{{ obj.platform.network_driver }}/main.j2",
                "backup_test_connectivity": True,
                "dynamic_group": dynamic_group.pk,
                "enable_intended": True,
                # sot_agg_query intentionally omitted.
            }
        )
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors["__all__"][0],
            "When Intended is enabled, you must define a `Sot agg query`, `Jinja repository` and `Jinja Template Path`.",
        )

    def test_clean_up(self):
        """Transactional custom model, unable to use `get_or_create`.

        Delete all objects created of GitRepository type.
        """
        GitRepository.objects.all().delete()
        self.assertEqual(GitRepository.objects.all().count(), 0)
