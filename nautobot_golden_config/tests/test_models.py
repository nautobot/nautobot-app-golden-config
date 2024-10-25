"""Unit tests for nautobot_golden_config models."""

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db.models.deletion import ProtectedError
from nautobot.apps.testing import TestCase
from nautobot.dcim.models import Platform
from nautobot.extras.models import DynamicGroup, GitRepository, GraphQLQuery, Status

from nautobot_golden_config.choices import RemediationTypeChoice
from nautobot_golden_config.models import (
    ConfigCompliance,
    ConfigPlan,
    ConfigRemove,
    ConfigReplace,
    GoldenConfigSetting,
    RemediationSetting,
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
