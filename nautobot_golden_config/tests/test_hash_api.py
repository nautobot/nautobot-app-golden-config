"""Unit tests for hash-related API endpoints in nautobot_golden_config."""

from django.urls import reverse
from nautobot.apps.testing import APITestCase, APIViewTestCases
from nautobot.dcim.models import Device
from rest_framework import status

from nautobot_golden_config import models
from nautobot_golden_config.tests.conftest import (
    create_device_data,
    create_feature_rule_json,
)


class ConfigHashGroupingAPITestCase(APIViewTestCases.APIViewTestCase):
    """Test API for ConfigHashGrouping."""

    model = models.ConfigHashGrouping

    def test_recreate_object_csv(self):
        """Skip this test due to JSON field serialization complexity."""
        self.skipTest("CSV recreate not supported due to JSONField config_content serialization differences")

    @classmethod
    def setUpTestData(cls):
        """Set up test data for ConfigHashGrouping API tests."""
        create_device_data()

        # Get devices created by conftest
        cls.device1 = Device.objects.get(name="Device 1")
        cls.device2 = Device.objects.get(name="Device 2")
        cls.device3 = Device.objects.get(name="Device 3")

        # Create compliance features and rules
        cls.feature1 = create_feature_rule_json(cls.device1, feature="TestFeature1")
        cls.feature2 = create_feature_rule_json(cls.device2, feature="TestFeature2")
        cls.feature3 = create_feature_rule_json(cls.device3, feature="TestFeature3")

        # Create ConfigCompliance objects (non-compliant) for hash relationships
        cls.compliance1 = models.ConfigCompliance.objects.create(
            device=cls.device1,
            rule=cls.feature1,
            compliance=False,
            actual='{"interface": "GigabitEthernet0/1", "description": "test1"}',
            intended='{"interface": "GigabitEthernet0/1", "description": "intended1"}',
        )
        cls.compliance2 = models.ConfigCompliance.objects.create(
            device=cls.device2,
            rule=cls.feature1,
            compliance=False,
            actual='{"interface": "GigabitEthernet0/1", "description": "test1"}',  # Same as compliance1
            intended='{"interface": "GigabitEthernet0/1", "description": "intended2"}',
        )
        cls.compliance3 = models.ConfigCompliance.objects.create(
            device=cls.device3,
            rule=cls.feature2,
            compliance=False,
            actual='{"interface": "GigabitEthernet0/2", "description": "test2"}',  # Different config
            intended='{"interface": "GigabitEthernet0/2", "description": "intended3"}',
        )

        # Get the ConfigHashGrouping objects that were automatically created
        cls.hash_groups = models.ConfigHashGrouping.objects.all()

        # Create additional compliance records to get at least 3 hash groups for bulk operations
        cls.compliance4 = models.ConfigCompliance.objects.create(
            device=cls.device1,
            rule=cls.feature2,
            compliance=False,
            actual='{"interface": "GigabitEthernet0/3", "description": "test3"}',
            intended='{"interface": "GigabitEthernet0/3", "description": "intended3"}',
        )

        # Create data for new objects - need different rules/configs since unique constraints exist
        cls.create_data = [
            {
                "rule": cls.feature3.pk,
                "config_hash": "abcd1234567890123456789012345678901234567890123456789012ff",
                "config_content": {"interface": "GigabitEthernet0/3", "description": "create_test1"},
            },
            {
                "rule": cls.feature2.pk,
                "config_hash": "bcde1234567890123456789012345678901234567890123456789012ff",
                "config_content": {"interface": "GigabitEthernet0/4", "description": "create_test2"},
            },
            {
                "rule": cls.feature1.pk,
                "config_hash": "cdef1234567890123456789012345678901234567890123456789012ff",
                "config_content": {"interface": "GigabitEthernet0/5", "description": "create_test3"},
            },
        ]

        cls.update_data = {
            "config_content": {"interface": "GigabitEthernet0/1", "description": "updated_test"},
        }

        cls.bulk_update_data = {
            "config_content": {"interface": "GigabitEthernet0/1", "description": "bulk_updated"},
        }


class ConfigComplianceHashAPITestCase(APIViewTestCases.APIViewTestCase):
    """Test API for ConfigComplianceHash."""

    model = models.ConfigComplianceHash

    def test_recreate_object_csv(self):
        """Skip this test due to complex FK relationships with config_group."""
        self.skipTest("CSV recreate not supported due to complex config_group foreign key relationships")

    @classmethod
    def setUpTestData(cls):
        """Set up test data for ConfigComplianceHash API tests."""
        create_device_data()

        # Get devices created by conftest
        cls.device1 = Device.objects.get(name="Device 1")
        cls.device2 = Device.objects.get(name="Device 2")
        cls.device3 = Device.objects.get(name="Device 3")

        # Create compliance features and rules
        cls.feature1 = create_feature_rule_json(cls.device1, feature="TestFeature1")
        cls.feature2 = create_feature_rule_json(cls.device2, feature="TestFeature2")
        cls.feature3 = create_feature_rule_json(cls.device3, feature="TestFeature3")

        # Create ConfigCompliance objects (non-compliant) for hash relationships
        cls.compliance1 = models.ConfigCompliance.objects.create(
            device=cls.device1,
            rule=cls.feature1,
            compliance=False,
            actual='{"interface": "GigabitEthernet0/1", "description": "test1"}',
            intended='{"interface": "GigabitEthernet0/1", "description": "intended1"}',
        )
        cls.compliance2 = models.ConfigCompliance.objects.create(
            device=cls.device2,
            rule=cls.feature2,
            compliance=False,
            actual='{"interface": "GigabitEthernet0/2", "description": "test2"}',
            intended='{"interface": "GigabitEthernet0/2", "description": "intended2"}',
        )
        cls.compliance3 = models.ConfigCompliance.objects.create(
            device=cls.device3,
            rule=cls.feature3,
            compliance=False,
            actual='{"interface": "GigabitEthernet0/3", "description": "test3"}',
            intended='{"interface": "GigabitEthernet0/3", "description": "intended3"}',
        )

        # Get the ConfigComplianceHash objects that were automatically created
        cls.hash_objects = models.ConfigComplianceHash.objects.all()

        # Create additional devices for create_data to avoid unique constraint violations
        cls.device4 = Device.objects.create(
            name="Device 4",
            device_type=cls.device1.device_type,
            role=cls.device1.role,
            location=cls.device1.location,
            platform=cls.device1.platform,
            status=cls.device1.status,
        )
        cls.device5 = Device.objects.create(
            name="Device 5",
            device_type=cls.device2.device_type,
            role=cls.device2.role,
            location=cls.device2.location,
            platform=cls.device2.platform,
            status=cls.device2.status,
        )
        cls.device6 = Device.objects.create(
            name="Device 6",
            device_type=cls.device3.device_type,
            role=cls.device3.role,
            location=cls.device3.location,
            platform=cls.device3.platform,
            status=cls.device3.status,
        )

        # Create data for new objects
        cls.create_data = [
            {
                "device": cls.device4.pk,
                "rule": cls.feature1.pk,
                "config_type": "actual",
                "config_hash": "abcd1234567890123456789012345678901234567890123456789012ff",
                "config_group": None,
            },
            {
                "device": cls.device5.pk,
                "rule": cls.feature2.pk,
                "config_type": "intended",
                "config_hash": "bcde1234567890123456789012345678901234567890123456789012ff",
                "config_group": None,
            },
            {
                "device": cls.device6.pk,
                "rule": cls.feature3.pk,
                "config_type": "actual",
                "config_hash": "cdef1234567890123456789012345678901234567890123456789012ff",
                "config_group": None,
            },
        ]

        cls.update_data = {
            "config_hash": "updated1234567890123456789012345678901234567890123456789012ff",
        }

        cls.bulk_update_data = {
            "config_hash": "bulk_upd1234567890123456789012345678901234567890123456789012ff",
        }

        cls.choices_fields = ["config_type"]


class ConfigHashGroupingListAPITest(APITestCase):
    """Test ConfigHashGrouping list API."""

    def setUp(self):
        """Create a superuser and token for API calls."""
        super().setUp()
        create_device_data()

        # Get devices created by conftest
        self.device1 = Device.objects.get(name="Device 1")
        self.device2 = Device.objects.get(name="Device 2")

        # Create compliance features and rules
        self.feature1 = create_feature_rule_json(self.device1, feature="TestFeature1")

        # Create ConfigCompliance objects (non-compliant) for hash relationships
        self.compliance1 = models.ConfigCompliance.objects.create(
            device=self.device1,
            rule=self.feature1,
            compliance=False,
            actual='{"interface": "GigabitEthernet0/1", "description": "test1"}',
            intended='{"interface": "GigabitEthernet0/1", "description": "intended1"}',
        )
        self.compliance2 = models.ConfigCompliance.objects.create(
            device=self.device2,
            rule=self.feature1,
            compliance=False,
            actual='{"interface": "GigabitEthernet0/1", "description": "test1"}',  # Same config as device1
            intended='{"interface": "GigabitEthernet0/1", "description": "intended2"}',
        )

        self.base_view = reverse("plugins-api:nautobot_golden_config-api:confighashgrouping-list")

    def test_config_hash_grouping_list_view(self):
        """Verify that ConfigHashGrouping objects can be listed."""
        self.add_permissions("nautobot_golden_config.view_confighashgrouping")
        response = self.client.get(self.base_view, **self.header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data["count"], 1)

    def test_config_hash_grouping_list_view_unauthorized(self):
        """Verify that ConfigHashGrouping list requires proper permissions."""
        response = self.client.get(self.base_view, **self.header)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_config_hash_grouping_detail_view(self):
        """Verify that ConfigHashGrouping detail view works."""
        self.add_permissions("nautobot_golden_config.view_confighashgrouping")
        hash_group = models.ConfigHashGrouping.objects.first()
        detail_url = reverse(
            "plugins-api:nautobot_golden_config-api:confighashgrouping-detail", kwargs={"pk": hash_group.pk}
        )
        response = self.client.get(detail_url, **self.header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], str(hash_group.id))
        self.assertEqual(str(response.data["rule"]["id"]), str(hash_group.rule.id))
        self.assertEqual(response.data["config_hash"], hash_group.config_hash)

    def test_config_hash_grouping_filter_by_rule(self):
        """Test filtering ConfigHashGrouping by rule."""
        self.add_permissions("nautobot_golden_config.view_confighashgrouping")
        response = self.client.get(f"{self.base_view}?rule={self.feature1.pk}", **self.header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data["count"], 1)
        # Verify all returned objects are for the correct rule
        for result in response.data["results"]:
            self.assertEqual(str(result["rule"]["id"]), str(self.feature1.id))


class ConfigComplianceHashListAPITest(APITestCase):
    """Test ConfigComplianceHash list API."""

    def setUp(self):
        """Create a superuser and token for API calls."""
        super().setUp()
        create_device_data()

        # Get devices created by conftest
        self.device1 = Device.objects.get(name="Device 1")
        self.device2 = Device.objects.get(name="Device 2")

        # Create compliance features and rules
        self.feature1 = create_feature_rule_json(self.device1, feature="TestFeature1")

        # Create ConfigCompliance objects (non-compliant) for hash relationships
        self.compliance1 = models.ConfigCompliance.objects.create(
            device=self.device1,
            rule=self.feature1,
            compliance=False,
            actual='{"interface": "GigabitEthernet0/1", "description": "test1"}',
            intended='{"interface": "GigabitEthernet0/1", "description": "intended1"}',
        )
        self.compliance2 = models.ConfigCompliance.objects.create(
            device=self.device2,
            rule=self.feature1,
            compliance=False,
            actual='{"interface": "GigabitEthernet0/2", "description": "test2"}',
            intended='{"interface": "GigabitEthernet0/2", "description": "intended2"}',
        )

        self.base_view = reverse("plugins-api:nautobot_golden_config-api:configcompliancehash-list")

    def test_config_compliance_hash_list_view(self):
        """Verify that ConfigComplianceHash objects can be listed."""
        self.add_permissions("nautobot_golden_config.view_configcompliancehash")
        response = self.client.get(self.base_view, **self.header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data["count"], 2)  # Should have at least actual and intended for each device

    def test_config_compliance_hash_list_view_unauthorized(self):
        """Verify that ConfigComplianceHash list requires proper permissions."""
        response = self.client.get(self.base_view, **self.header)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_config_compliance_hash_detail_view(self):
        """Verify that ConfigComplianceHash detail view works."""
        self.add_permissions("nautobot_golden_config.view_configcompliancehash")
        hash_obj = models.ConfigComplianceHash.objects.first()
        detail_url = reverse(
            "plugins-api:nautobot_golden_config-api:configcompliancehash-detail", kwargs={"pk": hash_obj.pk}
        )
        response = self.client.get(detail_url, **self.header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], str(hash_obj.id))
        self.assertEqual(str(response.data["device"]["id"]), str(hash_obj.device.id))
        self.assertEqual(str(response.data["rule"]["id"]), str(hash_obj.rule.id))
        self.assertEqual(response.data["config_type"], hash_obj.config_type)
        self.assertEqual(response.data["config_hash"], hash_obj.config_hash)

    def test_config_compliance_hash_filter_by_device(self):
        """Test filtering ConfigComplianceHash by device."""
        self.add_permissions("nautobot_golden_config.view_configcompliancehash")
        response = self.client.get(f"{self.base_view}?device={self.device1.pk}", **self.header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data["count"], 1)
        # Verify all returned objects are for the correct device
        for result in response.data["results"]:
            self.assertEqual(str(result["device"]["id"]), str(self.device1.id))

    def test_config_compliance_hash_filter_by_config_type(self):
        """Test filtering ConfigComplianceHash by config_type."""
        self.add_permissions("nautobot_golden_config.view_configcompliancehash")
        response = self.client.get(f"{self.base_view}?config_type=actual", **self.header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data["count"], 1)
        # Verify all returned objects have the correct config_type
        for result in response.data["results"]:
            self.assertEqual(result["config_type"], "actual")

    def test_config_compliance_hash_filter_by_rule(self):
        """Test filtering ConfigComplianceHash by rule."""
        self.add_permissions("nautobot_golden_config.view_configcompliancehash")
        response = self.client.get(f"{self.base_view}?rule={self.feature1.pk}", **self.header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data["count"], 1)
        # Verify all returned objects are for the correct rule
        for result in response.data["results"]:
            self.assertEqual(str(result["rule"]["id"]), str(self.feature1.id))


class ConfigHashGroupingCSVTest(APITestCase):
    """Test ConfigHashGrouping CSV export."""

    def setUp(self):
        super().setUp()
        self.add_permissions("nautobot_golden_config.view_confighashgrouping")
        self.url = reverse("plugins-api:nautobot_golden_config-api:confighashgrouping-list")

    def test_csv_export(self):
        """Test CSV export returns 200/OK."""
        response = self.client.get(f"{self.url}?format=csv", **self.header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("text/csv", response["content-type"])


class ConfigComplianceHashCSVTest(APITestCase):
    """Test ConfigComplianceHash CSV export."""

    def setUp(self):
        super().setUp()
        self.add_permissions("nautobot_golden_config.view_configcompliancehash")
        self.url = reverse("plugins-api:nautobot_golden_config-api:configcompliancehash-list")

    def test_csv_export(self):
        """Test CSV export returns 200/OK."""
        response = self.client.get(f"{self.url}?format=csv", **self.header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("text/csv", response["content-type"])
