"""Unit tests for nautobot_golden_config datasources."""

import os
import tempfile
from unittest.mock import MagicMock, Mock

import yaml
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from nautobot.apps.choices import LogLevelChoices
from nautobot.apps.testing import TransactionTestCase
from nautobot.dcim.models import Platform
from nautobot.extras.models import JobResult, Tag

from nautobot_golden_config.datasources import get_id_kwargs, get_tags, refresh_git_gc_properties
from nautobot_golden_config.exceptions import MissingReference, MultipleReferences
from nautobot_golden_config.models import ComplianceFeature, ComplianceRule, RemediationSetting


class GitPropertiesDatasourceTestCase(TestCase):
    """Test Git GC Properties datasource."""

    def setUp(self):
        """Setup Object."""
        self.platform = Platform.objects.create(name="example_platform")
        self.platform.network_driver = "example_platform"
        self.platform.save()
        self.compliance_feature = ComplianceFeature.objects.create(slug="example_feature")
        self.job_result = Mock()

    def test_get_id_kwargs_1(self):
        """Test simple get_id_kwargs 1."""
        initial_gc_config_item_dict = {"name": "some name"}
        gc_config_item_dict = initial_gc_config_item_dict.copy()
        id_kwargs = get_id_kwargs(
            gc_config_item_dict,
            (("name", "name"),),
            self.job_result,
        )
        self.assertEqual(id_kwargs, initial_gc_config_item_dict)
        self.assertEqual(gc_config_item_dict, {})

    def test_get_id_kwargs_2(self):
        """Test simple get_id_kwargs 2."""
        gc_config_item_dict = {"name": "some name", "description": "some description"}
        id_kwargs = get_id_kwargs(
            gc_config_item_dict,
            (("name", "name"),),
            self.job_result,
        )
        self.assertEqual(id_kwargs, {"name": "some name"})
        self.assertEqual(gc_config_item_dict, {"description": "some description"})

    def test_get_id_kwargs_3(self):
        """Test simple get_id_kwargs 3."""
        gc_config_item_dict = {"name": "some name", "description": "some description"}
        id_kwargs = get_id_kwargs(
            gc_config_item_dict,
            (),
            self.job_result,
        )
        self.assertEqual(id_kwargs, {})
        self.assertEqual(gc_config_item_dict, gc_config_item_dict)

    def test_get_id_kwargs_4(self):
        """Test simple get_id_kwargs ."""
        gc_config_item_dict = {"platform_network_driver": "invalid_platform"}
        with self.assertRaises(MissingReference):
            get_id_kwargs(
                gc_config_item_dict,
                (("platform", "platform_network_driver"),),
                self.job_result,
            )

    def test_get_id_kwargs_5(self):
        """Test simple get_id_kwargs 5."""
        gc_config_item_dict = {"platform_network_driver": "example_platform"}
        id_kwargs = get_id_kwargs(
            gc_config_item_dict,
            (("platform", "platform_network_driver"),),
            self.job_result,
        )
        self.assertEqual(id_kwargs, {"platform": self.platform})
        self.assertEqual(gc_config_item_dict, {})

    def test_get_id_kwargs_6(self):
        """Test simple get_id_kwargs 6."""
        gc_config_item_dict = {"feature_slug": "invalid_feature"}
        with self.assertRaises(MissingReference):
            get_id_kwargs(
                gc_config_item_dict,
                (("feature", "feature_slug"),),
                self.job_result,
            )

    def test_get_id_kwargs_7(self):
        """Test simple get_id_kwargs 7."""
        gc_config_item_dict = {"feature_slug": "example_feature"}
        id_kwargs = get_id_kwargs(
            gc_config_item_dict,
            (("feature", "feature_slug"),),
            self.job_result,
        )
        self.assertEqual(id_kwargs, {"feature": self.compliance_feature})
        self.assertEqual(gc_config_item_dict, {})

    def test_two_platforms_same_network_driver_exc(self):
        """Test multiple platforms using same network driver raises exception."""
        platform2 = Platform.objects.create(name="example_platform2")
        platform2.network_driver = "example_platform"
        platform2.save()
        gc_config_item_dict = {"platform_network_driver": "example_platform"}
        with self.assertRaises(MultipleReferences):
            get_id_kwargs(
                gc_config_item_dict,
                (("platform", "platform_network_driver"),),
                self.job_result,
            )

    def test_two_platforms_same_network_driver_two_keys(self):
        """Test platform name takes precedence over platform network driver 1."""
        gc_config_item_dict = {"platform_name": "example_platform", "platform_network_driver": "example_platform"}
        id_kwargs = get_id_kwargs(
            gc_config_item_dict,
            (("platform", "platform_name"),),
            self.job_result,
        )
        self.assertEqual(id_kwargs, {"platform": self.platform})
        self.assertEqual(gc_config_item_dict, {})

    def test_two_platforms_same_network_driver_two_keys_2(self):
        """Test platform name takes precedence over platform network driver 2."""
        platform2 = Platform.objects.create(name="example_platform2")
        platform2.network_driver = "example_platform"
        platform2.save()
        gc_config_item_dict = {"platform_name": "example_platform2", "platform_network_driver": "example_platform"}
        id_kwargs = get_id_kwargs(
            gc_config_item_dict,
            (("platform", "platform_name"),),
            self.job_result,
        )
        self.assertEqual(id_kwargs, {"platform": platform2})
        self.assertEqual(gc_config_item_dict, {})


class TestDatasources(TransactionTestCase):
    """Test Datasources."""

    def setUp(self):
        """Setup Object."""
        self.platform = Platform.objects.create(name="example_platform")
        self.platform.network_driver = "example_platform"
        self.platform.save()
        self.job_result = Mock()

    def test_refresh_git_gc_properties_1(self):
        """Test refresh_git_gc_properties with one platform."""
        repository_record = MagicMock()
        repository_record.filesystem_path = "nautobot_golden_config/tests/fixtures/datasource_mocks1"
        repository_record.provided_contents = "nautobot_golden_config.pluginproperties"
        job_result = JobResult()
        job_result.log = MagicMock(return_value=None)
        refresh_git_gc_properties(repository_record=repository_record, job_result=job_result)
        self.assertEqual(ComplianceFeature.objects.count(), 3)
        self.assertEqual(ComplianceRule.objects.count(), 3)
        self.assertEqual(RemediationSetting.objects.count(), 1)

    def test_refresh_git_gc_properties_2(self):
        """Test refresh_git_gc_properties with two platforms using same network driver."""
        platform2 = Platform.objects.create(name="example_platform2")
        platform2.network_driver = "example_platform"
        platform2.save()
        repository_record = MagicMock()
        repository_record.filesystem_path = "nautobot_golden_config/tests/fixtures/datasource_mocks1"
        repository_record.provided_contents = "nautobot_golden_config.pluginproperties"
        job_result = JobResult()
        job_result.log = MagicMock(return_value=None)
        with self.assertRaises(MultipleReferences):
            refresh_git_gc_properties(repository_record=repository_record, job_result=job_result)

    def test_refresh_git_gc_properties_3(self):
        """Test refresh_git_gc_properties with two platforms using same network driver."""
        platform2 = Platform.objects.create(name="example_platform2")
        platform2.network_driver = "example_platform"
        platform2.save()
        repository_record = MagicMock()
        repository_record.filesystem_path = "nautobot_golden_config/tests/fixtures/datasource_mocks2"
        repository_record.provided_contents = "nautobot_golden_config.pluginproperties"
        job_result = JobResult()
        job_result.log = MagicMock(return_value=None)
        refresh_git_gc_properties(repository_record=repository_record, job_result=job_result)
        self.assertEqual(ComplianceFeature.objects.count(), 3)
        self.assertEqual(ComplianceRule.objects.count(), 3)

    def test_refresh_git_gc_properties_tags(self):
        """Test that a tag scoped to the property's content type is assigned to the synced object."""
        tag = Tag(name="my_tag_name")
        tag.validated_save()
        tag.content_types.add(ContentType.objects.get_for_model(ComplianceFeature))
        repository_record = MagicMock()
        repository_record.filesystem_path = "nautobot_golden_config/tests/fixtures/datasource_mocks3"
        repository_record.provided_contents = "nautobot_golden_config.pluginproperties"
        job_result = JobResult()
        job_result.log = MagicMock(return_value=None)
        refresh_git_gc_properties(repository_record=repository_record, job_result=job_result)
        feature = ComplianceFeature.objects.get(name="tagged_feature")
        self.assertIn(tag, feature.tags.all())

    def test_refresh_git_gc_properties_tags_missing(self):
        """Test that referencing a non-existent tag skips the item and logs E3034."""
        repository_record = MagicMock()
        repository_record.filesystem_path = "nautobot_golden_config/tests/fixtures/datasource_mocks3"
        repository_record.provided_contents = "nautobot_golden_config.pluginproperties"
        job_result = JobResult()
        job_result.log = MagicMock(return_value=None)
        refresh_git_gc_properties(repository_record=repository_record, job_result=job_result)
        self.assertFalse(ComplianceFeature.objects.filter(name="tagged_feature").exists())
        logged_messages = [call.args[0] for call in job_result.log.call_args_list if call.args]
        self.assertTrue(any("E3034" in message for message in logged_messages))

    def test_refresh_git_gc_properties_tags_wrong_content_type(self):
        """Test that a tag not scoped to the property's content type skips the item and logs E3034."""
        tag = Tag(name="my_tag_name")
        tag.validated_save()
        tag.content_types.add(ContentType.objects.get_for_model(RemediationSetting))
        repository_record = MagicMock()
        repository_record.filesystem_path = "nautobot_golden_config/tests/fixtures/datasource_mocks3"
        repository_record.provided_contents = "nautobot_golden_config.pluginproperties"
        job_result = JobResult()
        job_result.log = MagicMock(return_value=None)
        refresh_git_gc_properties(repository_record=repository_record, job_result=job_result)
        self.assertFalse(ComplianceFeature.objects.filter(name="tagged_feature").exists())
        logged_messages = [call.args[0] for call in job_result.log.call_args_list if call.args]
        self.assertTrue(any("E3034" in message for message in logged_messages))

    def _sync_compliance_features(self, features):
        """Sync a temporary Git repository working tree providing the given compliance features."""
        with tempfile.TemporaryDirectory() as repo_path:
            feature_path = os.path.join(repo_path, "golden_config", "compliance_features")
            os.makedirs(feature_path)
            with open(os.path.join(feature_path, "all.yml"), "w", encoding="utf-8") as yaml_file:
                yaml.safe_dump(features, yaml_file)
            repository_record = MagicMock()
            repository_record.filesystem_path = repo_path
            repository_record.provided_contents = "nautobot_golden_config.pluginproperties"
            job_result = JobResult()
            job_result.log = MagicMock(return_value=None)
            refresh_git_gc_properties(repository_record=repository_record, job_result=job_result)
        return [call.args[0] for call in job_result.log.call_args_list if call.args]

    def _create_feature_tag(self, name):
        """Create a tag assignable to ComplianceFeature."""
        tag = Tag(name=name)
        tag.validated_save()
        tag.content_types.add(ContentType.objects.get_for_model(ComplianceFeature))
        return tag

    def test_refresh_git_gc_properties_tags_resync_removes_one(self):
        """Test that a tag removed from the list is removed from the object on resync."""
        tag_a = self._create_feature_tag("tag_a")
        tag_b = self._create_feature_tag("tag_b")
        feature = {"name": "tagged_feature", "slug": "tagged_feature"}
        self._sync_compliance_features([{**feature, "tags": [{"name": "tag_a"}, {"name": "tag_b"}]}])
        self.assertCountEqual(ComplianceFeature.objects.get(name="tagged_feature").tags.all(), [tag_a, tag_b])
        self._sync_compliance_features([{**feature, "tags": [{"name": "tag_b"}]}])
        self.assertCountEqual(ComplianceFeature.objects.get(name="tagged_feature").tags.all(), [tag_b])

    def test_refresh_git_gc_properties_tags_resync_removes_key(self):
        """Test that removing the tags key (or emptying it) removes the tags from the object on resync."""
        self._create_feature_tag("tag_a")
        feature = {"name": "tagged_feature", "slug": "tagged_feature"}
        for cleared in (feature, {**feature, "tags": []}, {**feature, "tags": None}):
            with self.subTest(cleared=cleared):
                self._sync_compliance_features([{**feature, "tags": [{"name": "tag_a"}]}])
                self.assertEqual(ComplianceFeature.objects.get(name="tagged_feature").tags.count(), 1)
                self._sync_compliance_features([dict(cleared)])
                self.assertEqual(ComplianceFeature.objects.get(name="tagged_feature").tags.count(), 0)

    def test_refresh_git_gc_properties_tags_invalid_reference(self):
        """Test that malformed tag references log E3034 and leave the object untouched instead of failing the sync."""
        tag_a = self._create_feature_tag("tag_a")
        feature = {"name": "tagged_feature", "slug": "tagged_feature"}
        self._sync_compliance_features([{**feature, "description": "original", "tags": [{"name": "tag_a"}]}])
        for invalid in (["tag_a"], "tag_a", [{"not_a_field": "tag_a"}], [{"name": "does_not_exist"}]):
            with self.subTest(invalid=invalid):
                logged_messages = self._sync_compliance_features(
                    [{**feature, "description": "changed", "tags": invalid}]
                )
                self.assertTrue(any("E3034" in message for message in logged_messages))
                synced = ComplianceFeature.objects.get(name="tagged_feature")
                self.assertEqual(synced.description, "original")
                self.assertCountEqual(synced.tags.all(), [tag_a])

    def test_refresh_git_gc_properties_bad_reference_skips_only_that_item(self):
        """Test that an item with an unresolvable reference does not prevent the rest of the file from syncing."""
        tag_a = self._create_feature_tag("tag_a")
        logged_messages = self._sync_compliance_features(
            [
                {"name": "first", "slug": "first", "tags": [{"name": "tag_a"}]},
                {"name": "broken", "slug": "broken", "tags": [{"name": "tag_a"}, {"name": "does_not_exist"}]},
                {"name": "last", "slug": "last", "tags": [{"name": "tag_a"}]},
            ]
        )
        self.assertTrue(any("E3034" in message for message in logged_messages))
        self.assertFalse(ComplianceFeature.objects.filter(name="broken").exists())
        for name in ("first", "last"):
            self.assertCountEqual(ComplianceFeature.objects.get(name=name).tags.all(), [tag_a])

    def test_refresh_git_gc_properties_reference_failures_logged_as_warning(self):
        """Test that reference failures are logged as warnings, as an error-level log entry fails the whole sync."""
        job_result = JobResult()
        job_result.log = MagicMock(return_value=None)
        with self.assertRaises(MissingReference):
            get_tags({"tags": [{"name": "does_not_exist"}]}, ComplianceFeature, job_result)
        self.assertEqual(job_result.log.call_args.kwargs["level_choice"], LogLevelChoices.LOG_WARNING)
