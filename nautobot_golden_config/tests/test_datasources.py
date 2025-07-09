"""Unit tests for nautobot_golden_config datasources."""

from unittest.mock import MagicMock, Mock

from django.test import TestCase
from nautobot.apps.testing import TransactionTestCase
from nautobot.dcim.models import Platform
from nautobot.extras.models import JobResult

from nautobot_golden_config.datasources import get_id_kwargs, refresh_git_gc_properties
from nautobot_golden_config.exceptions import MissingReference, MultipleReferences
from nautobot_golden_config.models import ComplianceFeature, ComplianceRule


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
