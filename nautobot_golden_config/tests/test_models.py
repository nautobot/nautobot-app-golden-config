"""Unit tests for nautobot_golden_config models."""

import json
import pathlib
from typing import Any
from unittest.mock import MagicMock, patch

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db.models.deletion import ProtectedError
from nautobot.apps.testing import TestCase
from nautobot.dcim.models import Platform
from nautobot.extras.models import DynamicGroup, GitRepository, GraphQLQuery, Status

from nautobot_golden_config.choices import RemediationTypeChoice
from nautobot_golden_config.models import (
    ApiRemediation,
    ConfigCompliance,
    ConfigPlan,
    ConfigRemove,
    ConfigReplace,
    DictKey,
    GoldenConfigSetting,
    RemediationSetting,
    _create_deepdiff_object,
    _get_hierconfig_remediation,
    _wrap_dict_keys,
)
from nautobot_golden_config.tests.conftest import create_git_repos

from .conftest import (
    create_config_compliance,
    create_device,
    create_feature_rule_cli_with_remediation,
    create_feature_rule_json,
    create_feature_rule_xml,
    create_job_result,
    create_saved_queries,
)

# pylint: disable=protected-access


class ConfigComplianceModelTestCase(TestCase):
    """Test CRUD operations for ConfigCompliance Model."""

    @classmethod
    def setUpTestData(cls):
        """Set up base objects."""
        cls.device = create_device()
        cls.compliance_rule_json = create_feature_rule_json(cls.device)
        cls.compliance_rule_xml = create_feature_rule_xml(cls.device)
        cls.compliance_rule_cli = create_feature_rule_cli_with_remediation(cls.device)

    def test_create_config_compliance_success_json(self):
        """Successful."""
        actual = {"foo": {"bar-1": "baz"}}
        intended = {"foo": {"bar-2": "baz"}}
        cc_obj = create_config_compliance(
            self.device, actual=actual, intended=intended, compliance_rule=self.compliance_rule_json
        )

        self.assertFalse(cc_obj.compliance)
        self.assertEqual(cc_obj.actual, {"foo": {"bar-1": "baz"}})
        self.assertEqual(cc_obj.intended, {"foo": {"bar-2": "baz"}})
        self.assertEqual(cc_obj.missing, ["root['foo']['bar-2']"])
        self.assertEqual(cc_obj.extra, ["root['foo']['bar-1']"])

    def test_create_config_compliance_success_xml(self):
        """Successful."""
        actual = "<root><foo><bar-1>notbaz</bar-1></foo></root>"
        intended = "<root><foo><bar-1>baz</bar-1></foo></root>"
        cc_obj = create_config_compliance(
            self.device, actual=actual, intended=intended, compliance_rule=self.compliance_rule_xml
        )

        self.assertFalse(cc_obj.compliance)
        self.assertEqual(cc_obj.actual, "<root><foo><bar-1>notbaz</bar-1></foo></root>")
        self.assertEqual(cc_obj.intended, "<root><foo><bar-1>baz</bar-1></foo></root>")
        self.assertEqual(cc_obj.missing, "/root/foo/bar-1[1], baz")
        self.assertEqual(cc_obj.extra, "/root/foo/bar-1[1], notbaz")

    def test_create_config_compliance_unique_failure(self):
        """Raises error when attempting to create duplicate."""
        ConfigCompliance.objects.create(
            device=self.device,
            rule=self.compliance_rule_json,
            actual={"foo": {"bar-1": "baz"}},
            intended={"foo": {"bar-2": "baz"}},
            missing={},
            extra={},
        )
        with self.assertRaises(ValidationError):
            ConfigCompliance.objects.create(
                device=self.device,
                rule=self.compliance_rule_json,
                compliance=False,
                actual={"foo": {"bar-1": "baz"}},
                intended={"foo": {"bar-2": "baz"}},
                missing={},
                extra={},
            )

    def test_create_config_compliance_success_compliant(self):
        """Successful."""
        cc_obj = ConfigCompliance.objects.create(
            device=self.device,
            rule=self.compliance_rule_json,
            actual={"foo": {"bar-1": "baz"}},
            intended={"foo": {"bar-1": "baz"}},
        )

        self.assertTrue(cc_obj.compliance)
        self.assertEqual(cc_obj.missing, "")
        self.assertEqual(cc_obj.extra, "")

    def test_config_compliance_signal_change_platform(self):
        """Make sure signal is working."""
        ConfigCompliance.objects.create(
            device=self.device,
            rule=self.compliance_rule_json,
            actual={"foo": {"bar-1": "baz"}},
            intended={"foo": {"bar-1": "baz"}},
        )
        self.assertEqual(ConfigCompliance.objects.filter(device=self.device).count(), 1)
        self.device.platform = Platform.objects.create(name="Platform Change")
        new_rule_json = create_feature_rule_json(self.device)

        ConfigCompliance.objects.create(
            device=self.device,
            rule=new_rule_json,
            actual={"foo": {"bar-1": "baz"}},
            intended={"foo": {"bar-1": "baz"}},
        )
        self.assertEqual(ConfigCompliance.objects.filter(device=self.device).count(), 1)

    def test_update_or_create(self):
        """We test this to ensure regression against
        https://docs.djangoproject.com/en/5.1/releases/4.2/#setting-update-fields-in-model-save-may-now-be-required."""

        remediation_setting = RemediationSetting.objects.create(
            platform=self.device.platform,
            remediation_type=RemediationTypeChoice.TYPE_HIERCONFIG,
        )

        cc_obj, _ = ConfigCompliance.objects.update_or_create(
            device=self.device,
            rule=self.compliance_rule_cli,
            defaults={
                "actual": "ntp 1.1.1.1\nntp 2.2.2.2",
                "intended": "ntp 1.1.1.1\nntp 3.3.3.3",
            },
        )

        self.assertFalse(cc_obj.compliance)
        self.assertFalse(cc_obj.compliance_int)
        self.assertEqual(cc_obj.missing, "ntp 3.3.3.3")
        self.assertEqual(cc_obj.extra, "ntp 2.2.2.2")
        self.assertEqual(cc_obj.remediation, "no ntp 2.2.2.2\nntp 3.3.3.3")
        self.assertFalse(cc_obj.ordered)

        remediation_setting.config_ordered = True
        remediation_setting.save()
        # We run again to ensure this works, the issue actually only shows on
        # when `update_fields` is set
        cc_obj_2, _ = ConfigCompliance.objects.update_or_create(
            device=self.device,
            rule=self.compliance_rule_cli,
            defaults={
                "actual": "ntp 1.1.1.1\nntp 2.2.2.2",
                "intended": "ntp 1.1.1.1\nntp 2.2.2.2",
            },
        )

        self.assertTrue(cc_obj_2.compliance)
        self.assertTrue(cc_obj_2.compliance_int)
        self.assertEqual(cc_obj_2.missing, "")
        self.assertEqual(cc_obj_2.extra, "")
        self.assertEqual(cc_obj_2.remediation, "")
        self.assertTrue(cc_obj_2.ordered)

        # Ensure that the .save() is not effected.

        cc_obj_3 = ConfigCompliance.objects.get(device=self.device, rule=self.compliance_rule_cli)
        cc_obj_3.intended = "ntp 1.1.1.1\nntp 3.3.3.3"
        cc_obj_3.save()

        self.assertFalse(cc_obj_3.compliance)
        self.assertFalse(cc_obj_3.compliance_int)
        self.assertEqual(cc_obj_3.missing, "ntp 3.3.3.3")
        self.assertEqual(cc_obj_3.extra, "ntp 2.2.2.2")
        self.assertEqual(cc_obj_3.remediation, "no ntp 2.2.2.2\nntp 3.3.3.3")


class GoldenConfigTestCase(TestCase):
    """Test GoldenConfig Model."""


class ComplianceRuleTestCase(TestCase):
    """Test ComplianceRule Model."""


class GoldenConfigSettingModelTestCase(TestCase):
    """Test GoldenConfigSetting Model."""

    @classmethod
    def setUpTestData(cls):
        """Get the golden config settings with the only allowed id."""
        create_git_repos()
        create_saved_queries()

        # Since we enforce a singleton pattern on this model, nuke the auto-created object.
        GoldenConfigSetting.objects.all().delete()
        cls.device_content_type = ContentType.objects.get(app_label="dcim", model="device")
        cls.dynamic_group = DynamicGroup.objects.create(
            name="test1 site site-4",
            content_type=cls.device_content_type,
            filter={},
        )

        cls.global_settings = GoldenConfigSetting.objects.create(  # pylint: disable=attribute-defined-outside-init
            name="test",
            slug="test",
            weight=1000,
            description="Test Description.",
            backup_path_template="{{ obj.location.parant.name }}/{{obj.name}}.cfg",
            intended_path_template="{{ obj.location.name }}/{{ obj.name }}.cfg",
            backup_test_connectivity=True,
            jinja_repository=GitRepository.objects.get(name="test-jinja-repo-1"),
            jinja_path_template="{{ obj.platform.name }}/main.j2",
            backup_repository=GitRepository.objects.get(name="test-backup-repo-1"),
            intended_repository=GitRepository.objects.get(name="test-intended-repo-1"),
            dynamic_group=cls.dynamic_group,
        )

    def test_absolute_url_success(self):
        """Verify that get_absolute_url() returns the expected URL."""
        url_string = self.global_settings.get_absolute_url()
        # Changed from assertEqual to assertIn to account for trailing slash added in later versions.
        self.assertIn(f"/plugins/golden-config/golden-config-setting/{self.global_settings.pk}", url_string)

    def test_good_graphql_query_invalid_starts_with(self):
        """Valid graphql query, however invalid in the usage with golden config app."""
        self.global_settings.sot_agg_query = GraphQLQuery.objects.get(name="GC-SoTAgg-Query-3")
        with self.assertRaises(ValidationError) as error:
            self.global_settings.clean()
        self.assertEqual(error.exception.message, "The GraphQL query must start with exactly `query ($device_id: ID!)`")

    def test_good_graphql_query_validate_starts_with(self):
        """Ensure clean() method returns None when valid query is sent through."""
        self.global_settings.sot_agg_query = GraphQLQuery.objects.get(name="GC-SoTAgg-Query-1")
        self.assertEqual(self.global_settings.clean(), None)

    def test_get_for_device(self):
        """Test get_for_device method on GoldenConfigSettingManager."""
        device = create_device()

        # test that the highest weight GoldenConfigSetting is returned
        other_dynamic_group = DynamicGroup.objects.create(
            name="test get_for_device dg",
            content_type=self.device_content_type,
            filter={"name": [device.name]},
        )
        other_dynamic_group.update_cached_members()
        other_settings = GoldenConfigSetting.objects.create(
            name="test other",
            slug="testother",
            weight=100,
            description="Test Description.",
            backup_path_template="{{ obj.location.parant.name }}/{{obj.name}}.cfg",
            intended_path_template="{{ obj.location.name }}/{{ obj.name }}.cfg",
            backup_test_connectivity=True,
            jinja_repository=GitRepository.objects.get(name="test-jinja-repo-1"),
            jinja_path_template="{{ obj.platform.name }}/main.j2",
            backup_repository=GitRepository.objects.get(name="test-backup-repo-1"),
            intended_repository=GitRepository.objects.get(name="test-intended-repo-1"),
            dynamic_group=other_dynamic_group,
        )

        self.dynamic_group.update_cached_members()
        if hasattr(device, "_dynamic_groups"):  # clear Device.dynamic_groups cache in nautobot <2.3
            delattr(device, "_dynamic_groups")
        self.assertEqual(GoldenConfigSetting.objects.get_for_device(device), self.global_settings)

        other_settings.weight = 2000
        other_settings.save()
        self.assertEqual(GoldenConfigSetting.objects.get_for_device(device), other_settings)

        # test that no GoldenConfigSetting is returned when the device is not in the dynamic group
        self.dynamic_group.filter = {"name": [f"{device.name} nomatch"]}
        other_dynamic_group.filter = {"name": [f"{device.name} nomatch"]}
        self.dynamic_group.save()
        other_dynamic_group.save()
        self.dynamic_group.update_cached_members()
        other_dynamic_group.update_cached_members()
        if hasattr(device, "_dynamic_groups"):  # clear Device.dynamic_groups cache in nautobot <2.3
            delattr(device, "_dynamic_groups")
        self.assertIsNone(GoldenConfigSetting.objects.get_for_device(device))

    def test_get_jinja_template_path_for_device(self):
        """Test get_jinja_template_path_for_device method on GoldenConfigSetting."""
        device = create_device()
        self.assertEqual(
            self.global_settings.get_jinja_template_path_for_device(device),
            f"{self.global_settings.jinja_repository.filesystem_path}/Platform 1/main.j2",
        )
        self.global_settings.jinja_repository = None
        self.global_settings.save()
        self.assertIsNone(self.global_settings.get_jinja_template_path_for_device(device))


class GoldenConfigSettingGitModelTestCase(TestCase):
    """Test GoldenConfigSetting Model."""

    @classmethod
    def setUpTestData(cls) -> None:
        """Setup test data."""
        create_git_repos()

        # Since we enforced a singleton pattern on this model in 0.9 release migrations, nuke any auto-created objects.
        GoldenConfigSetting.objects.all().delete()
        content_type = ContentType.objects.get(app_label="dcim", model="device")
        dynamic_group = DynamicGroup.objects.create(
            name="test1 site site-4",
            content_type=content_type,
            filter={},
        )

        # Create fresh new object, populate accordingly.
        cls.golden_config = GoldenConfigSetting.objects.create(  # pylint: disable=attribute-defined-outside-init
            name="test",
            slug="test",
            weight=1000,
            description="Test Description.",
            backup_path_template="{{ obj.location.parant.name }}/{{obj.name}}.cfg",
            intended_path_template="{{ obj.location.name }}/{{ obj.name }}.cfg",
            backup_test_connectivity=True,
            jinja_repository=GitRepository.objects.get(name="test-jinja-repo-1"),
            jinja_path_template="{{ obj.platform.name }}/main.j2",
            backup_repository=GitRepository.objects.get(name="test-backup-repo-1"),
            intended_repository=GitRepository.objects.get(name="test-intended-repo-1"),
            dynamic_group=dynamic_group,
        )

    def test_model_success(self):
        """Create a new instance of the GoldenConfigSettings model."""
        self.assertEqual(self.golden_config.name, "test")
        self.assertEqual(self.golden_config.slug, "test")
        self.assertEqual(self.golden_config.weight, 1000)
        self.assertEqual(self.golden_config.description, "Test Description.")
        self.assertEqual(self.golden_config.backup_path_template, "{{ obj.location.parant.name }}/{{obj.name}}.cfg")
        self.assertEqual(self.golden_config.intended_path_template, "{{ obj.location.name }}/{{ obj.name }}.cfg")
        self.assertTrue(self.golden_config.backup_test_connectivity)
        self.assertEqual(self.golden_config.jinja_repository, GitRepository.objects.get(name="test-jinja-repo-1"))
        self.assertEqual(self.golden_config.jinja_path_template, "{{ obj.platform.name }}/main.j2")
        self.assertEqual(self.golden_config.backup_repository, GitRepository.objects.get(name="test-backup-repo-1"))
        self.assertEqual(self.golden_config.intended_repository, GitRepository.objects.get(name="test-intended-repo-1"))

    def test_removing_git_repos(self):
        """Ensure we cannot remove the Git Repository objects while still attached to GC setting."""
        with self.assertRaises(ProtectedError):
            GitRepository.objects.all().delete()

    def test_clean_up(self):
        """Delete all objects created of GoldenConfigSetting type."""
        GoldenConfigSetting.objects.all().delete()
        self.assertEqual(GoldenConfigSetting.objects.all().count(), 0)


class ConfigRemoveModelTestCase(TestCase):
    """Test ConfigRemove Model."""

    @classmethod
    def setUpTestData(cls):
        """Setup Object."""
        cls.platform = Platform.objects.create(name="Cisco IOS", network_driver="cisco_ios")
        cls.line_removal = ConfigRemove.objects.create(
            name="foo", platform=cls.platform, description="foo bar", regex="^Back.*"
        )

    def test_add_line_removal_entry(self):
        """Test Add Object."""
        self.assertEqual(self.line_removal.name, "foo")
        self.assertEqual(self.line_removal.description, "foo bar")
        self.assertEqual(self.line_removal.regex, "^Back.*")

    def test_edit_line_removal_entry(self):
        """Test Edit Object."""
        new_name = "Line Remove"
        new_desc = "Testing Remove Running Config Line"
        new_regex = "^Running.*"
        self.line_removal.name = new_name
        self.line_removal.description = new_desc
        self.line_removal.regex = new_regex
        self.line_removal.save()

        self.assertEqual(self.line_removal.name, new_name)
        self.assertEqual(self.line_removal.description, new_desc)
        self.assertEqual(self.line_removal.regex, new_regex)


class ConfigReplaceModelTestCase(TestCase):
    """Test ConfigReplace Model."""

    @classmethod
    def setUpTestData(cls):
        """Setup Object."""
        cls.platform = Platform.objects.create(name="Cisco IOS", network_driver="cisco_ios")
        cls.line_replace = ConfigReplace.objects.create(
            name="foo",
            platform=cls.platform,
            description="foo bar",
            regex=r"username(\S+)",
            replace="<redacted>",
        )

    def test_add_line_replace_entry(self):
        """Test Add Object."""
        self.assertEqual(self.line_replace.name, "foo")
        self.assertEqual(self.line_replace.description, "foo bar")
        self.assertEqual(self.line_replace.regex, r"username(\S+)")
        self.assertEqual(self.line_replace.replace, "<redacted>")

    def test_edit_line_replace_entry(self):
        """Test Edit Object."""
        new_name = "Line Replacement"
        new_desc = "Testing Replacing Config Line"
        new_regex = r"password(\S+)"
        self.line_replace.name = new_name
        self.line_replace.description = new_desc
        self.line_replace.regex = new_regex
        self.line_replace.save()

        self.assertEqual(self.line_replace.name, new_name)
        self.assertEqual(self.line_replace.description, new_desc)
        self.assertEqual(self.line_replace.regex, new_regex)
        self.assertEqual(self.line_replace.replace, "<redacted>")


class ConfigPlanModelTestCase(TestCase):
    """Test ConfigPlan Model."""

    @classmethod
    def setUpTestData(cls):
        """Setup Object."""
        cls.device = create_device()
        cls.rule = create_feature_rule_json(cls.device)
        cls.feature = cls.rule.feature
        cls.status = Status.objects.get(name="Not Approved")
        cls.job_result = create_job_result()

    def test_create_config_plan_intended(self):
        """Test Create Object."""
        config_plan = ConfigPlan.objects.create(
            device=self.device,
            plan_type="intended",
            config_set="test intended config",
            change_control_id="1234",
            change_control_url="https://1234.example.com/",
            status=self.status,
            plan_result_id=self.job_result.id,
        )
        config_plan.feature.add(self.feature)
        config_plan.validated_save()
        self.assertEqual(config_plan.device, self.device)
        self.assertEqual(config_plan.feature.first(), self.feature)
        self.assertEqual(config_plan.config_set, "test intended config")
        self.assertEqual(config_plan.change_control_id, "1234")
        self.assertEqual(config_plan.status, self.status)
        self.assertEqual(config_plan.plan_type, "intended")

    def test_create_config_plan_intended_multiple_features(self):
        """Test Create Object."""
        rule2 = create_feature_rule_json(self.device, feature="feature2")
        config_plan = ConfigPlan.objects.create(
            device=self.device,
            plan_type="intended",
            config_set="test intended config",
            change_control_id="1234",
            change_control_url="https://1234.example.com/",
            status=self.status,
            plan_result_id=self.job_result.id,
        )
        config_plan.feature.set([self.feature, rule2.feature])
        config_plan.validated_save()
        self.assertEqual(config_plan.device, self.device)
        self.assertIn(self.feature.id, config_plan.feature.all().values_list("id", flat=True))
        self.assertIn(rule2.feature.id, config_plan.feature.all().values_list("id", flat=True))
        self.assertEqual(config_plan.config_set, "test intended config")
        self.assertEqual(config_plan.change_control_id, "1234")
        self.assertEqual(config_plan.status, self.status)
        self.assertEqual(config_plan.plan_type, "intended")

    def test_create_config_plan_missing(self):
        """Test Create Object."""
        config_plan = ConfigPlan.objects.create(
            device=self.device,
            plan_type="missing",
            config_set="test missing config",
            change_control_id="2345",
            change_control_url="https://2345.example.com/",
            status=self.status,
            plan_result_id=self.job_result.id,
        )
        config_plan.feature.add(self.feature)
        config_plan.validated_save()
        self.assertEqual(config_plan.device, self.device)
        self.assertEqual(config_plan.feature.first(), self.feature)
        self.assertEqual(config_plan.config_set, "test missing config")
        self.assertEqual(config_plan.change_control_id, "2345")
        self.assertEqual(config_plan.status, self.status)
        self.assertEqual(config_plan.plan_type, "missing")

    def test_create_config_plan_remediation(self):
        """Test Create Object."""
        config_plan = ConfigPlan.objects.create(
            device=self.device,
            plan_type="remediation",
            config_set="test remediation config",
            change_control_id="3456",
            change_control_url="https://3456.example.com/",
            status=self.status,
            plan_result_id=self.job_result.id,
        )
        config_plan.feature.add(self.feature)
        config_plan.validated_save()
        self.assertEqual(config_plan.device, self.device)
        self.assertEqual(config_plan.feature.first(), self.feature)
        self.assertEqual(config_plan.config_set, "test remediation config")
        self.assertEqual(config_plan.change_control_id, "3456")
        self.assertEqual(config_plan.status, self.status)
        self.assertEqual(config_plan.plan_type, "remediation")

    def test_create_config_plan_manual(self):
        """Test Create Object."""
        config_plan = ConfigPlan.objects.create(
            device=self.device,
            plan_type="manual",
            config_set="test manual config",
            plan_result_id=self.job_result.id,
        )
        self.assertEqual(config_plan.device, self.device)
        self.assertEqual(config_plan.config_set, "test manual config")
        self.assertEqual(config_plan.plan_type, "manual")


class RemediationSettingModelTestCase(TestCase):
    """Test Remediation Setting Model."""

    @classmethod
    def setUpTestData(cls):
        """Setup Object."""
        cls.platform = Platform.objects.create(name="Cisco IOS", network_driver="cisco_ios")
        cls.remediation_options = {
            "optionA": "someValue",
            "optionB": "someotherValue",
            "optionC": "anotherValue",
        }

    def test_create_remediation_setting_hier(self):
        """Test Create Hier Remediation Setting."""
        remediation_setting = RemediationSetting.objects.create(
            platform=self.platform,
            remediation_type=RemediationTypeChoice.TYPE_HIERCONFIG,
            remediation_options=self.remediation_options,
        )
        self.assertEqual(remediation_setting.platform, self.platform)
        self.assertEqual(remediation_setting.remediation_type, RemediationTypeChoice.TYPE_HIERCONFIG)
        self.assertEqual(remediation_setting.remediation_options, self.remediation_options)

    def test_create_remediation_setting_custom(self):
        """Test Create Custom Remediation Setting."""
        remediation_setting = RemediationSetting.objects.create(
            platform=self.platform,
            remediation_type=RemediationTypeChoice.TYPE_CUSTOM,
            remediation_options=self.remediation_options,
        )
        self.assertEqual(remediation_setting.platform, self.platform)
        self.assertEqual(remediation_setting.remediation_type, RemediationTypeChoice.TYPE_CUSTOM)
        self.assertEqual(remediation_setting.remediation_options, self.remediation_options)

    def test_create_remediation_setting_default_values(self):
        """Test Create Default Remediation Setting"""
        remediation_setting = RemediationSetting.objects.create(
            platform=self.platform,
        )
        self.assertEqual(remediation_setting.platform, self.platform)
        self.assertEqual(remediation_setting.remediation_type, RemediationTypeChoice.TYPE_HIERCONFIG)
        self.assertEqual(remediation_setting.remediation_options, {})


class GetHierConfigRemediationTestCase(TestCase):
    """Test _get_hierconfig_remediation function."""

    def test_successful_remediation(self):
        """Test successful remediation generation."""
        device = create_device()
        compliance_rule_cli = create_feature_rule_cli_with_remediation(device)

        RemediationSetting.objects.create(
            platform=device.platform,
            remediation_type=RemediationTypeChoice.TYPE_HIERCONFIG,
            remediation_options={},
        )
        config_compliance = ConfigCompliance(
            device=device,
            rule=compliance_rule_cli,
            actual="interface Ethernet1\n  no shutdown",
            intended="interface Ethernet1\n  description Test\n  no shutdown\n",
        )
        remediation = _get_hierconfig_remediation(config_compliance)

        self.assertIsInstance(remediation, str)
        self.assertIn("interface Ethernet1\n  description Test", remediation)

    def test_successful_remediation_with_options(self):
        """Test successful remediation generation with options (Issue #1061)."""
        device = create_device()
        compliance_rule_cli = create_feature_rule_cli_with_remediation(device)

        remediation_options = {"idempotent_commands": [{"lineage": [{"startswith": "foo"}]}]}
        actual = "foo test"
        intended = "foo bar"

        RemediationSetting.objects.create(
            platform=device.platform,
            remediation_type=RemediationTypeChoice.TYPE_HIERCONFIG,
            remediation_options=remediation_options,
        )
        config_compliance = ConfigCompliance(
            device=device,
            rule=compliance_rule_cli,
            actual=actual,
            intended=intended,
        )
        remediation = _get_hierconfig_remediation(config_compliance)
        self.assertIsInstance(remediation, str)
        self.assertEqual(remediation, intended)

    def test_remediation_options_merge(self):
        """Test that remediation options are merged with the default options (Issue #915)."""
        device = create_device()
        compliance_rule_cli = create_feature_rule_cli_with_remediation(device)
        # This adds 'foo' as an idempotent command,
        # but should not override the existing idempotent command 'errdisable recovery interval'.
        remediation_options = {"idempotent_commands": [{"lineage": [{"startswith": "foo"}]}]}
        actual = "errdisable recovery interval 100\n!\nfoo test"
        intended = "errdisable recovery interval 200\n!\nfoo bar"
        expected = "errdisable recovery interval 200\nfoo bar"
        RemediationSetting.objects.create(
            platform=device.platform,
            remediation_type=RemediationTypeChoice.TYPE_HIERCONFIG,
            remediation_options=remediation_options,
        )
        config_compliance = ConfigCompliance(
            device=device,
            rule=compliance_rule_cli,
            actual=actual,
            intended=intended,
        )
        remediation = _get_hierconfig_remediation(config_compliance)
        self.assertIsInstance(remediation, str)
        self.assertEqual(remediation, expected)

    def test_platform_not_supported_by_hierconfig(self):
        """Test error when platform is not supported by hierconfig."""
        device = create_device()
        device.platform.network_driver = "unsupported_driver"
        device.platform.save()

        compliance_rule_cli = create_feature_rule_cli_with_remediation(device)

        config_compliance = ConfigCompliance(
            device=device,
            rule=compliance_rule_cli,
            actual="interface Ethernet1\n  no shutdown",
            intended="interface Ethernet1\n  description Test\n  no shutdown\n",
        )

        # Validate that calling the function raises a ValidationError
        with self.assertRaises(ValidationError) as context:
            _get_hierconfig_remediation(config_compliance)

        self.assertIn("not supported by hierconfig", str(context.exception))

    def test_no_remediation_settings_defined(self):
        """Test error when no remediation settings are defined for the platform."""
        device = create_device()
        compliance_rule_cli = create_feature_rule_cli_with_remediation(device)

        config_compliance = ConfigCompliance(
            device=device,
            rule=compliance_rule_cli,
            actual="interface Ethernet1\n  no shutdown",
            intended="interface Ethernet1\n  description Test\n  no shutdown\n",
        )
        # Make sure no remediation settings exist for this platform
        RemediationSetting.objects.filter(platform=device.platform).delete()

        with self.assertRaises(ValidationError) as context:
            _get_hierconfig_remediation(config_compliance)

        self.assertIn("has no Remediation Settings defined", str(context.exception))

    @patch("nautobot_golden_config.models.hconfig_v2_os_v3_platform_mapper")
    @patch("nautobot_golden_config.models.get_hconfig")
    @patch("nautobot_golden_config.models.WorkflowRemediation")
    def test_hierconfig_instantiation_error(self, mock_workflow_remediation, mock_get_hconfig, mock_mapper):
        """Test error when HierConfig instantiation fails."""
        device = create_device()
        compliance_rule_cli = create_feature_rule_cli_with_remediation(device)

        RemediationSetting.objects.create(
            platform=device.platform,
            remediation_type=RemediationTypeChoice.TYPE_HIERCONFIG,
        )

        # Set up mocks to raise an exception
        mock_mapper.return_value = "ios"
        mock_get_hconfig.side_effect = Exception("Test exception")

        # We won't reach the WorkflowRemediation instantiation, but configure it anyway
        # to satisfy pylint
        mock_instance = mock_workflow_remediation.return_value
        mock_instance.remediation_config_filtered_text.return_value = "mock remediation"

        # Create a mock ConfigCompliance object
        config_compliance = ConfigCompliance(
            device=device,
            rule=compliance_rule_cli,
            actual="interface Ethernet1\n  no shutdown",
            intended="interface Ethernet1\n  description Test\n  no shutdown\n",
        )

        # Validate that calling the function raises an Exception
        with self.assertRaises(Exception) as context:
            _get_hierconfig_remediation(config_compliance)

        self.assertIn("Cannot instantiate HierConfig", str(context.exception))

        # Verify mock usage
        mock_mapper.assert_called_once_with("ios")
        mock_get_hconfig.assert_called_once()
        # WorkflowRemediation should never be called since get_hconfig raises exception
        mock_workflow_remediation.assert_not_called()


def load_fixture(filename: str) -> Any:
    """Load a JSON fixture from a file.

    Args:
        filename (str): Path to the JSON file.

    Returns:
        Any: The loaded JSON data.
    """
    with pathlib.Path(filename).open(encoding="utf-8") as f:
        return json.load(fp=f)


class TestDictKey(TestCase):
    """Test cases for the DictKey class."""

    def test_str_and_repr(self):
        k = DictKey("foo")
        self.assertEqual(str(k), "foo")
        self.assertEqual(repr(k), "DictKey('foo')")


class TestWrapDictKeys(TestCase):
    """Test cases for the _wrap_dict_keys function."""

    def test_wrap_dict_keys(self):
        obj = {"a": 1, "b": {"c": 2}, "d": [3, {"e": 4}]}
        wrapped = _wrap_dict_keys(obj)
        # Check top-level keys are DictKey
        self.assertTrue(all(isinstance(k, DictKey) for k in wrapped.keys()))
        # Check nested dict keys are DictKey
        self.assertTrue(all(isinstance(k, DictKey) for k in wrapped[DictKey("b")].keys()))
        # Check list elements are preserved
        self.assertEqual(wrapped[DictKey("d")][0], 3)
        self.assertTrue(isinstance(wrapped[DictKey("d")][1], dict))
        self.assertTrue(isinstance(list(wrapped[DictKey("d")][1].keys())[0], DictKey))


class TestCreateDeepDiffObject(TestCase):
    """Test cases for the _create_deepdiff_object function."""

    def test_deepdiff_object(self):
        a = {"foo": 1, "bar": 2}
        b = {"foo": 1, "bar": 3}
        dd = _create_deepdiff_object(a, b)
        self.assertIn("values_changed", dd)


class TestApiRemediation(TestCase):
    """Test ApiRemediation class using mocks and fixture files."""

    @classmethod
    def setUpClass(cls):
        cls.base_fixtures_path = "nautobot_golden_config/tests/fixtures/remediation/"
        cls.dict_intended_config = load_fixture(filename=f"{cls.base_fixtures_path}dict_intended_config.json")
        cls.dict_actual_config = load_fixture(filename=f"{cls.base_fixtures_path}dict_actual_config.json")
        cls.list_intended_config = load_fixture(filename=f"{cls.base_fixtures_path}list_intended_config.json")
        cls.list_actual_config = load_fixture(filename=f"{cls.base_fixtures_path}list_actual_config.json")
        cls.dict_config_context = load_fixture(filename=f"{cls.base_fixtures_path}dict_config_context.json")
        cls.list_config_context = load_fixture(filename=f"{cls.base_fixtures_path}list_config_context.json")
        super().setUpClass()

    def setUp(self):
        rule = MagicMock()
        rule.feature.name = "feature"
        rule.config_type = "json"
        device = MagicMock()
        device.get_config_context.return_value = {"feature_remediation": self.dict_config_context}
        compliance_obj = MagicMock()
        compliance_obj.rule = rule
        compliance_obj.device = device
        compliance_obj.intended = self.dict_intended_config
        compliance_obj.actual = self.dict_actual_config
        self.compliance_obj = compliance_obj
        self.api = ApiRemediation(self.compliance_obj)

    def test_dict_remediation_delta(self):
        api = ApiRemediation(compliance_obj=self.compliance_obj)
        payload = api.api_remediation()
        self.assertTrue(isinstance(payload, str))
        if payload:
            data = json.loads(payload)
            self.assertIn("feature", data)
            self.assertIsInstance(data["feature"], dict)

    def test_list_remediation_delta(self):
        rule = MagicMock()
        rule.feature.name = "feature"
        rule.config_type = "json"
        device = MagicMock()
        device.get_config_context.return_value = {"feature_remediation": self.list_config_context}
        compliance_obj = MagicMock()
        compliance_obj.rule = rule
        compliance_obj.device = device
        compliance_obj.intended = self.list_intended_config
        compliance_obj.actual = self.list_actual_config
        self.compliance_obj = compliance_obj
        api = ApiRemediation(compliance_obj=self.compliance_obj)
        payload = api.api_remediation()
        self.assertTrue(isinstance(payload, str))
        if payload:
            data = json.loads(payload)
            self.assertIn("feature", data)
            self.assertIsInstance(data["feature"], list)

    def test_clean_diff(self):
        a = {"feature": {"x": 1, "y": 0}}
        b = {"feature": {"x": 1, "y": 2}}
        dd = _create_deepdiff_object(a, b)
        cleaned = self.api._clean_diff(dd)
        self.assertIn("feature", cleaned)
        self.assertIn("y", cleaned["feature"])

    def test_api_remediation_delta(self):
        payload = self.api.api_remediation()
        # Should be a JSON string with only changed fields
        if payload:
            data = json.loads(payload)
            self.assertIn("feature", data)
            # The actual changed fields depend on the fixture content
            self.assertIsInstance(data["feature"], dict)

    def test_dict_remediation_full_intended(self):
        # If remediate_full_intended is True, should return full intended config
        rule = MagicMock()
        rule.feature.name = "feature"
        rule.config_type = "json"
        device = MagicMock()
        device.get_config_context.return_value = {"remediate_full_intended": True}
        compliance_obj = MagicMock()
        compliance_obj.rule = rule
        compliance_obj.device = device
        compliance_obj.intended = self.dict_intended_config
        compliance_obj.actual = self.dict_actual_config
        api = ApiRemediation(compliance_obj)
        payload = api.api_remediation()
        self.assertEqual(json.loads(payload), self.dict_intended_config)

    def test_list_remediation_full_intended(self):
        # If remediate_full_intended is True, should return full intended config
        rule = MagicMock()
        rule.feature.name = "feature"
        rule.config_type = "json"
        device = MagicMock()
        device.get_config_context.return_value = {"remediate_full_intended": True}
        compliance_obj = MagicMock()
        compliance_obj.rule = rule
        compliance_obj.device = device
        compliance_obj.intended = self.list_intended_config
        compliance_obj.actual = self.list_actual_config
        api = ApiRemediation(compliance_obj)
        payload = api.api_remediation()
        self.assertEqual(json.loads(payload), self.list_intended_config)

    def test_api_remediation_no_context(self):
        rule = MagicMock()
        rule.feature.name = "feature"
        rule.config_type = "json"
        device = MagicMock()
        device.get_config_context.return_value = {}
        compliance_obj = MagicMock()
        compliance_obj.rule = rule
        compliance_obj.device = device
        compliance_obj.intended = {"feature": {"x": 1}}
        compliance_obj.actual = {"feature": {"x": 0}}
        api = ApiRemediation(compliance_obj)
        with self.assertRaises(ValidationError):
            api.api_remediation()

    def test_api_remediation_no_diff(self):
        # Should return empty string if no diff
        rule = MagicMock()
        rule.feature.name = "feature"
        rule.config_type = "json"
        device = MagicMock()
        device.get_config_context.return_value = {"feature_remediation": self.dict_config_context}
        compliance_obj = MagicMock()
        compliance_obj.rule = rule
        compliance_obj.device = device
        compliance_obj.intended = {"feature": {"x": 1}}
        compliance_obj.actual = {"feature": {"x": 1}}
        api = ApiRemediation(compliance_obj)
        payload = api.api_remediation()
        self.assertEqual(payload, "")
