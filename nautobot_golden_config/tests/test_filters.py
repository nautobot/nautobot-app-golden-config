"""Unit tests for nautobot_golden_config models."""

from unittest import skip
from django.test import TestCase

from nautobot.dcim.models import Device, Platform
from nautobot_golden_config import filters, models

from .conftest import create_feature_rule_json, create_device_data


class ConfigComplianceModelTestCase(TestCase):  # pylint: disable=too-many-public-methods
    """Test filtering operations for ConfigCompliance Model."""

    queryset = models.ConfigCompliance.objects.all()
    filterset = filters.ConfigComplianceFilterSet

    def setUp(self):
        """Set up base objects."""
        create_device_data()
        self.dev01 = Device.objects.get(name="Device 1")
        dev02 = Device.objects.get(name="Device 2")
        self.dev03 = Device.objects.get(name="Device 3")
        dev04 = Device.objects.get(name="Device 4")
        dev05 = Device.objects.get(name="Device 5")
        dev06 = Device.objects.get(name="Device 6")

        feature_dev01 = create_feature_rule_json(self.dev01)
        feature_dev02 = create_feature_rule_json(dev02)
        feature_dev03 = create_feature_rule_json(self.dev03)
        feature_dev05 = create_feature_rule_json(dev05, feature="baz")
        feature_dev06 = create_feature_rule_json(dev06, feature="bar")

        updates = [
            {"device": self.dev01, "feature": feature_dev01},
            {"device": dev02, "feature": feature_dev02},
            {"device": self.dev03, "feature": feature_dev03},
            {"device": dev04, "feature": feature_dev01},
            {"device": dev05, "feature": feature_dev05},
            {"device": dev06, "feature": feature_dev06},
        ]
        for update in updates:
            models.ConfigCompliance.objects.create(
                device=update["device"],
                rule=update["feature"],
                actual={"foo": {"bar-1": "baz"}},
                intended={"foo": {"bar-1": "baz"}},
            )

    def test_id(self):
        """Test filtering by ID (primary key)."""
        params = {"id": str(self.queryset.values_list("pk", flat=True)[0])}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_full(self):
        """Test without filtering to ensure all devices have been added."""
        self.assertEqual(self.queryset.count(), 6)

    def test_device(self):
        """Test filtering by Device."""
        params = {"device": [self.dev01.name]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
        params = {"device": [self.dev01.id]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_search(self):
        """Test filtering by Q search value."""
        params = {"q": self.dev01.name[-1:]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_location(self):
        """Test filtering by Location Name."""
        params = {"location": [self.dev01.location.name]}
        filter_result = self.filterset(params, self.queryset).qs
        self.assertEqual(filter_result.count(), 4)
        # Devices are assigned to 2 different Locations that share the same Name
        unique_locations = {result.device.location for result in filter_result}
        self.assertEqual(len(unique_locations), 2)

    def test_location_id(self):
        """Test filtering by Location ID."""
        params = {"location_id": [self.dev01.location.id]}
        filter_result = self.filterset(params, self.queryset).qs
        self.assertEqual(filter_result.count(), 3)
        # Devices are assigned to 1 Location since ID is used instead of Name
        unique_locations = {result.device.location for result in filter_result}
        self.assertEqual(len(unique_locations), 1)

    @skip("This will not work until https://github.com/nautobot/nautobot/issues/4329 is resolved")
    def test_location_parent_name(self):
        """Test filtering by Location Parent Name."""
        params = {"location": [self.dev03.location.parent.name]}
        filter_result = self.filterset(params, self.queryset).qs
        self.assertEqual(filter_result.count(), 2)
        # Devices are assigned to 2 different Locations that share the same Parent
        unique_locations = {result.device.location for result in filter_result}
        self.assertEqual(len(unique_locations), 2)
        device_names = {result.device.name for result in filter_result}
        self.assertEqual({"Device 3", "Device 5"}, device_names)

    def test_location_parent_id(self):
        """Test filtering by Location Parent ID."""
        params = {"location_id": [self.dev03.location.parent.id]}
        filter_result = self.filterset(params, self.queryset).qs
        self.assertEqual(filter_result.count(), 2)
        # Devices are assigned to 2 different Locations that share the same Parent
        unique_locations = {result.device.location for result in filter_result}
        self.assertEqual(len(unique_locations), 2)
        device_names = {result.device.name for result in filter_result}
        self.assertEqual({"Device 3", "Device 5"}, device_names)

    def test_tenant(self):
        """Test filtering by Tenant."""
        params = {"tenant": [self.dev01.tenant.name]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 4)
        params = {"tenant": [self.dev01.tenant.id]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 4)

    def test_tenant_group(self):
        """Test filtering by Tenant Group Name."""
        params = {"tenant_group": [self.dev01.tenant.tenant_group.name]}
        filter_result = self.filterset(params, self.queryset).qs
        self.assertEqual(filter_result.count(), 4)

    def test_tenant_group_id(self):
        """Test filtering by Tenant Group ID."""
        params = {"tenant_group": [self.dev01.tenant.tenant_group.id]}
        filter_result = self.filterset(params, self.queryset).qs
        self.assertEqual(filter_result.count(), 4)

    def test_tenant_group_parent(self):
        """Test filtering by Tenant Group Parent Name."""
        params = {"tenant_group": [self.dev01.tenant.tenant_group.parent.name]}
        filter_result = self.filterset(params, self.queryset).qs
        self.assertEqual(filter_result.count(), 5)

    def test_tenant_group_parent_id(self):
        """Test filtering by Tenant Group Parent ID."""
        params = {"tenant_group": [self.dev01.tenant.tenant_group.parent.id]}
        filter_result = self.filterset(params, self.queryset).qs
        self.assertEqual(filter_result.count(), 5)

    def test_rack(self):
        """Test filtering by Rack."""
        params = {"rack": [self.dev01.rack.name]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {"rack": [self.dev01.rack.id]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_rack_group(self):
        """Test filtering by Rack Group Name."""
        params = {"rack_group": [self.dev01.rack.rack_group.name]}
        filter_result = self.filterset(params, self.queryset).qs
        self.assertEqual(filter_result.count(), 3)
        # Devices are assigned to 2 different Rack Groups that share the same Name
        unique_rack_groups = {result.device.rack.rack_group for result in filter_result}
        self.assertEqual(len(unique_rack_groups), 2)

    def test_rack_group_id(self):
        """Test filtering by Rack Group ID."""
        params = {"rack_group_id": [self.dev01.rack.rack_group.id]}
        filter_result = self.filterset(params, self.queryset).qs
        self.assertEqual(filter_result.count(), 2)
        # Devices are assigned to 1 Rack Group since ID is used instead of Name
        unique_rack_groups = {result.device.rack.rack_group for result in filter_result}
        self.assertEqual(len(unique_rack_groups), 1)

    @skip("This will not work until https://github.com/nautobot/nautobot/issues/4329 is resolved")
    def test_rack_group_parent_name(self):
        """Test filtering by Rack Group Parent Group Name."""
        params = {"rack_group": [self.dev01.rack.rack_group.parent.name]}
        filter_result = self.filterset(params, self.queryset).qs
        self.assertEqual(filter_result.count(), 3)
        # Devices are assigned to 2 different Rack Groups that share the same Parent
        unique_rack_groups = {result.device.rack.rack_group for result in filter_result}
        self.assertEqual(len(unique_rack_groups), 2)
        device_names = {result.device.name for result in filter_result}
        self.assertEqual({"Device 1", "Device 4", "Device 6"}, device_names)

    def test_rack_group_parent_id(self):
        """Test filtering by Rack Group Parent Group ID."""
        params = {"rack_group_id": [self.dev01.rack.rack_group.parent.id]}
        filter_result = self.filterset(params, self.queryset).qs
        self.assertEqual(filter_result.count(), 3)
        # Devices are assigned to 2 different Rack Groups that share the same Parent
        unique_rack_groups = {result.device.rack.rack_group for result in filter_result}
        self.assertEqual(len(unique_rack_groups), 2)
        device_names = {result.device.name for result in filter_result}
        self.assertEqual({"Device 1", "Device 4", "Device 6"}, device_names)

    def test_role(self):
        params = {"role": [self.dev01.role.name]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 4)
        params = {"role": [self.dev01.role.id]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 4)

    def test_platform(self):
        """Test filtering by Platform."""
        params = {"platform": [self.dev01.platform.name]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 4)
        params = {"platform": [self.dev01.platform.id]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 4)

    def test_manufacturer(self):
        """Test filtering by Manufacturer."""
        params = {"manufacturer": [self.dev01.device_type.manufacturer.name]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 4)
        params = {"manufacturer": [self.dev01.device_type.manufacturer.id]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 4)

    def test_device_type(self):
        """Test filtering by Device Type."""
        params = {"device_type": [self.dev01.device_type.model]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 4)
        params = {"device_type": [self.dev01.device_type.id]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 4)

    def test_device_status(self):
        """Test filtering by Device Status."""
        params = {"device_status": [self.dev01.status.name]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 4)


class GoldenConfigModelTestCase(ConfigComplianceModelTestCase):
    """Test filtering operations for GoldenConfig Model."""

    queryset = models.GoldenConfig.objects.all()
    filterset = filters.GoldenConfigFilterSet

    def setUp(self):
        """Set up base objects."""
        create_device_data()
        self.dev01 = Device.objects.get(name="Device 1")
        dev02 = Device.objects.get(name="Device 2")
        self.dev03 = Device.objects.get(name="Device 3")
        dev04 = Device.objects.get(name="Device 4")
        dev05 = Device.objects.get(name="Device 5")
        dev06 = Device.objects.get(name="Device 6")

        updates = [self.dev01, dev02, self.dev03, dev04, dev05, dev06]
        for update in updates:
            models.GoldenConfig.objects.create(
                device=update,
            )


class ConfigRemoveModelTestCase(TestCase):
    """Test filtering operations for ConfigRemove Model."""

    queryset = models.ConfigRemove.objects.all()
    filterset = filters.ConfigRemoveFilterSet

    def setUp(self):
        """Setup Object."""
        self.platform1 = Platform.objects.create(name="Platform 1")
        platform2 = Platform.objects.create(name="Platform 2")
        self.obj1 = models.ConfigRemove.objects.create(
            name="Remove 1", platform=self.platform1, description="Description 1", regex="^Remove 1"
        )
        models.ConfigRemove.objects.create(
            name="Remove 2", platform=self.platform1, description="Description 2", regex="^Remove 2"
        )
        models.ConfigRemove.objects.create(
            name="Remove 3", platform=platform2, description="Description 3", regex="^Remove 3"
        )

    def test_id(self):
        """Test filtering by ID (primary key)."""
        params = {"id": str(self.queryset.values_list("pk", flat=True)[0])}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_full(self):
        """Test without filtering to ensure all have been added."""
        self.assertEqual(self.queryset.count(), 3)

    def test_name(self):
        """Test filtering by Name."""
        params = {"name": self.obj1.name}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_search(self):
        """Test filtering by Q search value."""
        params = {"q": self.obj1.name[-1:]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_platform(self):
        """Test filtering by Platform."""
        params = {"platform": [self.platform1.name]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {"platform": [self.platform1.id]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)


class ConfigReplaceModelTestCase(ConfigRemoveModelTestCase):
    """Test filtering operations for ConfigReplace Model."""

    queryset = models.ConfigReplace.objects.all()
    filterset = filters.ConfigReplaceFilterSet

    def setUp(self):
        """Setup Object."""
        self.platform1 = Platform.objects.create(name="Platform 1")
        platform2 = Platform.objects.create(name="Platform 2")
        self.obj1 = models.ConfigReplace.objects.create(
            name="Remove 1",
            platform=self.platform1,
            description="Description 1",
            regex="^Remove 1",
            replace="Replace 1",
        )
        models.ConfigReplace.objects.create(
            name="Remove 2",
            platform=self.platform1,
            description="Description 2",
            regex="^Remove 2",
            replace="Replace 2",
        )
        models.ConfigReplace.objects.create(
            name="Remove 3", platform=platform2, description="Description 3", regex="^Remove 3", replace="Replace 3"
        )


class ComplianceRuleModelTestCase(ConfigRemoveModelTestCase):
    """Test filtering operations for ComplianceRule Model."""

    queryset = models.ComplianceRule.objects.all()
    filterset = filters.ComplianceRuleFilterSet

    def setUp(self):
        """Setup Object."""
        self.platform1 = Platform.objects.create(name="Platform 1")
        platform2 = Platform.objects.create(name="Platform 2")
        feature1 = models.ComplianceFeature.objects.create(name="Feature 1", slug="feature-1")
        feature2 = models.ComplianceFeature.objects.create(name="Feature 2", slug="feature-2")
        self.obj1 = models.ComplianceRule.objects.create(
            platform=self.platform1, feature=feature1, config_type="cli", config_ordered=True, match_config="config 1"
        )
        models.ComplianceRule.objects.create(
            platform=self.platform1, feature=feature2, config_type="cli", config_ordered=True, match_config="config 2"
        )
        models.ComplianceRule.objects.create(
            platform=platform2, feature=feature1, config_type="cli", config_ordered=True, match_config="config 3"
        )

    def test_name(self):
        """Override since there is no name on this model, but keeping DRY."""

    def test_search(self):
        """Test filtering by Q search value."""
        params = {"q": "2"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)


class ComplianceFeatureModelTestCase(TestCase):
    """Test filtering operations for ComplianceFeature Model."""

    queryset = models.ComplianceFeature.objects.all()
    filterset = filters.ComplianceFeatureFilterSet

    def setUp(self):
        """Setup Object."""
        self.obj1 = models.ComplianceFeature.objects.create(name="Feature 1", slug="feature-1")
        models.ComplianceFeature.objects.create(name="Feature 2", slug="feature-2")
        models.ComplianceFeature.objects.create(name="Feature 3", slug="feature-3")

    def test_full(self):
        """Test without filtering to ensure all have been added."""
        self.assertEqual(self.queryset.count(), 3)

    def test_id(self):
        """Test filtering by ID (primary key)."""
        params = {"id": str(self.queryset.values_list("pk", flat=True)[0])}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_name(self):
        """Test filtering by Name."""
        params = {"name": self.obj1.name}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_search(self):
        """Test filtering by Q search value."""
        params = {"q": self.obj1.name[-1:]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
