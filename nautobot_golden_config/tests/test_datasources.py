"""Unit tests for nautobot_golden_config datasources."""

from unittest.mock import Mock
from django.test import TestCase

from nautobot.dcim.models import Platform
from nautobot_golden_config.models import ComplianceFeature
from nautobot_golden_config.datasources import get_id_kwargs, MissingReference


class GitPropertiesDatasourceTestCase(TestCase):
    """Test Git GC Properties datasource."""

    def setUp(self):
        """Setup Object."""
        self.platform = Platform.objects.create(slug="example_platform")
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
        gc_config_item_dict = {"platform_slug": "invalid_platform"}
        with self.assertRaises(MissingReference):
            get_id_kwargs(
                gc_config_item_dict,
                (("platform", "platform_slug"),),
                self.job_result,
            )

    def test_get_id_kwargs_5(self):
        """Test simple get_id_kwargs 5."""
        gc_config_item_dict = {"platform_slug": "example_platform"}
        id_kwargs = get_id_kwargs(
            gc_config_item_dict,
            (("platform", "platform_slug"),),
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
