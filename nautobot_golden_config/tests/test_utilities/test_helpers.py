"""Unit tests for nautobot_golden_config utilities helpers."""

from unittest.mock import MagicMock, patch

from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.template import engines
from jinja2 import exceptions as jinja_errors
from nautobot.dcim.models import Device, Platform, Site
from nautobot.extras.models import DynamicGroup, GitRepository, GraphQLQuery, Status, Tag
from nornir_nautobot.exceptions import NornirNautobotException
from nornir_nautobot.utils.logger import NornirLogger
from nautobot_golden_config.models import GoldenConfigSetting
from nautobot_golden_config.tests.conftest import create_device, create_helper_repo, create_orphan_device
from nautobot_golden_config.utilities.helper import (
    get_device_to_settings_map,
    get_job_filter,
    null_to_empty,
    render_jinja_template,
)


class HelpersTest(TestCase):  # pylint: disable=too-many-instance-attributes
    """Test Helper Functions."""

    def setUp(self):
        """Setup a reusable mock object to pass into GitRepo."""
        self.repository_obj = MagicMock()
        self.repository_obj.path = "/fake/path"
        GitRepository.objects.all().delete()
        create_helper_repo(name="backup-parent_region-1", provides="backupconfigs")
        create_helper_repo(name="intended-parent_region-1", provides="intendedconfigs")
        create_helper_repo(name="test-jinja-repo", provides="jinjatemplate")

        create_helper_repo(name="backup-parent_region-2", provides="backupconfigs")
        create_helper_repo(name="intended-parent_region-2", provides="intendedconfigs")
        create_helper_repo(name="test-jinja-repo-2", provides="jinjatemplate")

        create_helper_repo(name="backup-parent_region-3", provides="backupconfigs")
        create_helper_repo(name="intended-parent_region-3", provides="intendedconfigs")
        create_helper_repo(name="test-jinja-repo-3", provides="jinjatemplate")

        # Since we enforce a singleton pattern on this model, nuke the auto-created object.
        GoldenConfigSetting.objects.all().delete()

        self.content_type = ContentType.objects.get(app_label="dcim", model="device")

        dynamic_group1 = DynamicGroup.objects.create(
            name="test1 site site-4",
            slug="test1-site-site-4",
            content_type=self.content_type,
            filter={"site": ["site-4"]},
        )
        dynamic_group2 = DynamicGroup.objects.create(
            name="test2 site site-4",
            slug="test2-site-site-4",
            content_type=self.content_type,
            filter={"site": ["site-4"]},
        )
        dynamic_group3 = DynamicGroup.objects.create(
            name="test3 site site-4",
            slug="test3-site-site-4",
            content_type=self.content_type,
            filter={},
        )
        graphql_query = GraphQLQuery.objects.create(
            name="testing",
            query="""
              query ($device_id: ID!) {
                device(id: $device_id){
                  name
                }
              }
            """,
        )
        self.test_settings_a = GoldenConfigSetting.objects.create(
            name="test_a",
            slug="test_a",
            description="test_a",
            weight=1000,
            backup_repository=GitRepository.objects.get(name="backup-parent_region-1"),
            intended_repository=GitRepository.objects.get(name="intended-parent_region-1"),
            jinja_repository=GitRepository.objects.get(name="test-jinja-repo"),
            # Limit scope to orphaned device only
            dynamic_group=dynamic_group1,
            sot_agg_query=graphql_query,
        )

        self.test_settings_b = GoldenConfigSetting.objects.create(
            name="test_b",
            slug="test_b",
            description="test_b",
            weight=2000,
            backup_repository=GitRepository.objects.get(name="backup-parent_region-2"),
            intended_repository=GitRepository.objects.get(name="intended-parent_region-2"),
            jinja_repository=GitRepository.objects.get(name="test-jinja-repo-2"),
            # Limit scope to orphaned device only
            dynamic_group=dynamic_group2,
            sot_agg_query=graphql_query,
        )

        self.test_settings_c = GoldenConfigSetting.objects.create(
            name="test_c",
            slug="test_c",
            description="test_c",
            weight=1000,
            backup_repository=GitRepository.objects.get(name="backup-parent_region-3"),
            intended_repository=GitRepository.objects.get(name="intended-parent_region-3"),
            jinja_repository=GitRepository.objects.get(name="test-jinja-repo-3"),
            dynamic_group=dynamic_group3,
            sot_agg_query=graphql_query,
        )

        # Device.objects.all().delete()
        create_device(name="test_device")
        create_orphan_device(name="orphan_device")
        self.job_result = MagicMock()
        self.data = MagicMock()
        self.logger = NornirLogger(__name__, self.job_result, self.data)
        self.device_to_settings_map = get_device_to_settings_map(queryset=Device.objects.all())

    def test_null_to_empty_null(self):
        """Ensure None returns with empty string."""
        result = null_to_empty(None)
        self.assertEqual(result, "")

    def test_null_to_empty_val(self):
        """Ensure if not None input is returned."""
        result = null_to_empty("test")
        self.assertEqual(result, "test")

    @patch("nautobot.dcim.models.Device")
    def test_render_jinja_template_success(self, mock_device):
        """Simple success test to return template."""
        worker = render_jinja_template(mock_device, "logger", "fake-template-contents")
        self.assertEqual(worker, "fake-template-contents")

    @patch("nautobot.dcim.models.Device")
    def test_render_jinja_template_success_render_context(self, mock_device):
        """Test that device object is passed to template context."""
        platform = "mock_platform"
        mock_device.platform = platform
        rendered_template = render_jinja_template(mock_device, "logger", "{{ obj.platform }}")
        self.assertEqual(rendered_template, platform)

    @patch("nautobot.dcim.models.Device")
    def test_render_jinja_template_success_with_filter(self, mock_device):
        """Test custom template and jinja filter are accessible."""
        rendered_template = render_jinja_template(mock_device, "logger", "{{ data | return_a }}")
        self.assertEqual(rendered_template, "a")

    @patch("nautobot.dcim.models.Device")
    def test_render_filters_work(self, mock_device):
        """Test Jinja filters are still there."""
        # This has failed because of import issues in the past, see #607 for an example failure and fix.
        self.assertIn("is_ip", engines["jinja"].env.filters)
        self.assertIn("humanize_speed", engines["jinja"].env.filters)
        rendered_template = render_jinja_template(mock_device, "logger", "{{ '10.1.1.1' | is_ip }}")
        self.assertEqual(rendered_template, "True")
        rendered_template = render_jinja_template(mock_device, "logger", "{{ 100000 | humanize_speed }}")
        self.assertEqual(rendered_template, "100 Mbps")

    @patch("nornir_nautobot.utils.logger.NornirLogger")
    @patch("nautobot.dcim.models.Device", spec=Device)
    def test_render_jinja_template_exceptions_undefined(self, mock_device, mock_nornir_logger):
        """Use fake obj key to cause UndefinedError from Jinja2 Template."""
        with self.assertRaises(NornirNautobotException):
            with self.assertRaises(jinja_errors.UndefinedError):
                render_jinja_template(mock_device, mock_nornir_logger, "{{ obj.fake }}")
        mock_nornir_logger.log_failure.assert_called_once()

    @patch("nornir_nautobot.utils.logger.NornirLogger")
    @patch("nautobot.dcim.models.Device")
    def test_render_jinja_template_exceptions_syntaxerror(self, mock_device, mock_nornir_logger):
        """Use invalid templating to cause TemplateSyntaxError from Jinja2 Template."""
        with self.assertRaises(NornirNautobotException):
            with self.assertRaises(jinja_errors.TemplateSyntaxError):
                render_jinja_template(mock_device, mock_nornir_logger, "{{ obj.fake }")
        mock_nornir_logger.log_failure.assert_called_once()

    @patch("nornir_nautobot.utils.logger.NornirLogger")
    @patch("nautobot.dcim.models.Device")
    @patch("nautobot_golden_config.utilities.helper.render_jinja2")
    def test_render_jinja_template_exceptions_templateerror(self, template_mock, mock_device, mock_nornir_logger):
        """Cause issue to cause TemplateError form Jinja2 Template."""
        with self.assertRaises(NornirNautobotException):
            with self.assertRaises(jinja_errors.TemplateError):
                template_mock.side_effect = jinja_errors.TemplateRuntimeError
                render_jinja_template(mock_device, mock_nornir_logger, "template")
        mock_nornir_logger.log_failure.assert_called_once()

    def test_get_backup_repository_dir_success(self):
        """Verify that we successfully look up the path from a provided repo object."""
        device = Device.objects.get(name="test_device")
        backup_directory = self.device_to_settings_map[device.id].backup_repository.filesystem_path
        self.assertEqual(backup_directory, "/opt/nautobot/git/backup-parent_region-3")

        device = Device.objects.get(name="orphan_device")
        backup_directory = self.device_to_settings_map[device.id].backup_repository.filesystem_path
        self.assertEqual(backup_directory, "/opt/nautobot/git/backup-parent_region-2")

    def test_get_intended_repository_dir_success(self):
        """Verify that we successfully look up the path from a provided repo object."""
        device = Device.objects.get(name="test_device")
        intended_directory = self.device_to_settings_map[device.id].intended_repository.filesystem_path
        self.assertEqual(intended_directory, "/opt/nautobot/git/intended-parent_region-3")

        device = Device.objects.get(name="orphan_device")
        intended_directory = self.device_to_settings_map[device.id].intended_repository.filesystem_path
        self.assertEqual(intended_directory, "/opt/nautobot/git/intended-parent_region-2")

    def test_get_job_filter_no_data_success(self):
        """Verify we get two devices returned when providing no data."""
        result = get_job_filter()
        self.assertEqual(result.count(), 2)

    def test_get_job_filter_site_success(self):
        """Verify we get a single device returned when providing specific site."""
        result = get_job_filter(data={"site": Site.objects.filter(slug="site-4")})
        self.assertEqual(result.count(), 1)

    def test_get_job_filter_device_object_success(self):
        """Verify we get a single device returned when providing single device object."""
        result = get_job_filter(data={"device": Device.objects.get(name="test_device")})
        self.assertEqual(result.count(), 1)

    def test_get_job_filter_device_filter_success(self):
        """Verify we get a single device returned when providing single device filter."""
        result = get_job_filter(data={"device": Device.objects.filter(name="test_device")})
        self.assertEqual(result.count(), 1)

    def test_get_job_filter_tag_success(self):
        """Verify we get a single device returned when providing tag filter that matches on device."""
        result = get_job_filter(data={"tag": Tag.objects.filter(name="Orphaned")})
        self.assertEqual(result.count(), 1)

    def test_get_job_filter_tag_success_and_logic(self):
        """Verify we get a single device returned when providing multiple tag filter that matches on device."""
        device = Device.objects.get(name="orphan_device")
        device_2 = Device.objects.get(name="test_device")
        content_type = ContentType.objects.get(app_label="dcim", model="device")
        tag, _ = Tag.objects.get_or_create(name="second-tag", slug="second-tag")
        tag.content_types.add(content_type)
        device.tags.add(tag)
        device_2.tags.add(tag)
        # Default tag logic is an `AND` not and `OR`.
        result = get_job_filter(data={"tag": Tag.objects.filter(name__in=["second-tag", "Orphaned"])})
        self.assertEqual(device.tags.count(), 2)
        self.assertEqual(device_2.tags.count(), 1)
        self.assertEqual(result.count(), 1)

    def test_get_job_filter_status_success(self):
        """Verify we get a single device returned when providing status filter that matches on device."""
        result = get_job_filter(data={"status": Status.objects.filter(name="Offline")})
        self.assertEqual(result.count(), 1)

    def test_get_job_filter_multiple_status_success(self):
        """Verify we get a0 devices returned matching multiple status'."""
        result = get_job_filter(data={"status": Status.objects.filter(name__in=["Offline", "Failed"])})
        self.assertEqual(result.count(), 2)

    def test_get_job_filter_base_queryset_raise(self):
        """Verify we get raise for having a base_qs with no objects due to bad Golden Config Setting scope."""
        Platform.objects.create(name="Placeholder Platform", slug="placeholder-platform")
        for golden_settings in GoldenConfigSetting.objects.all():
            dynamic_group = DynamicGroup.objects.create(
                name=f"{golden_settings.name} group",
                slug=f"{golden_settings.slug}-group",
                content_type=self.content_type,
                filter={"platform": ["placeholder-platform"]},
            )
            golden_settings.dynamic_group = dynamic_group
            golden_settings.validated_save()
        with self.assertRaises(NornirNautobotException) as failure:
            get_job_filter()
        self.assertEqual(
            failure.exception.args[0],
            "The base queryset didn't find any devices. Please check the Golden Config Setting scope.",
        )

    def test_get_job_filter_filtered_devices_raise(self):
        """Verify we get raise for having providing site that doesn't have any devices in scope."""
        Site.objects.create(name="New Site", slug="new-site", status=Status.objects.get(slug="active"))
        with self.assertRaises(NornirNautobotException) as failure:
            get_job_filter(data={"site": Site.objects.filter(name="New Site")})
        self.assertEqual(
            failure.exception.args[0],
            "The provided job parameters didn't match any devices detected by the Golden Config scope. Please check the scope defined within Golden Config Settings or select the correct job parameters to correctly match devices.",
        )

    def test_get_job_filter_device_no_platform_raise(self):
        """Verify we get raise for not having a platform set on a device."""
        device = Device.objects.get(name="test_device")
        device.platform = None
        device.status = Status.objects.get(slug="active")
        device.validated_save()
        with self.assertRaises(NornirNautobotException) as failure:
            get_job_filter()
        self.assertEqual(
            failure.exception.args[0],
            "The following device(s) test_device have no platform defined. Platform is required.",
        )

    def test_device_to_settings_map(self):
        """Verify Golden Config Settings are properly mapped to devices."""
        test_device = Device.objects.get(name="test_device")
        orphan_device = Device.objects.get(name="orphan_device")
        self.assertEqual(self.device_to_settings_map[test_device.id], self.test_settings_c)
        self.assertEqual(self.device_to_settings_map[orphan_device.id], self.test_settings_b)
        self.assertEqual(get_device_to_settings_map(queryset=Device.objects.none()), {})
