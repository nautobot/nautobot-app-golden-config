"""Unit tests for nautobot_golden_config models."""

from unittest import skip
from django.test import TestCase

from nautobot.dcim.models import Device, Platform
from nautobot_golden_config import filters, models

from .conftest import create_feature_rule_json, create_device_data


class ConfigComplianceModelTestCase(TestCase):
    """Test filtering operations for ConfigCompliance Model."""

    queryset = models.ConfigCompliance.objects.all()
    filterset = filters.ConfigComplianceFilterSet

    def setUp(self):
        """Set up base objects."""
        create_device_data()
        self.dev01 = Device.objects.get(name="Device 1")
        dev02 = Device.objects.get(name="Device 2")
        dev03 = Device.objects.get(name="Device 3")
        dev04 = Device.objects.get(name="Device 4")

        feature_dev01 = create_feature_rule_json(self.dev01)
        feature_dev02 = create_feature_rule_json(dev02)
        feature_dev03 = create_feature_rule_json(dev03)

        updates = [
            {"device": self.dev01, "feature": feature_dev01},
            {"device": dev02, "feature": feature_dev02},
            {"device": dev03, "feature": feature_dev03},
            {"device": dev04, "feature": feature_dev01},
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
        params = {"id": self.queryset.values_list("pk", flat=True)[0]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_full(self):
        """Test without filtering to ensure all devices have been added."""
        self.assertEqual(self.queryset.count(), 4)

    def test_device(self):
        """Test filtering by Device."""
        params = {"device": [self.dev01.name]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
        params = {"device_id": [self.dev01.id]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_search(self):
        """Test filtering by Q search value."""
        params = {"q": self.dev01.name[-1:]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_region(self):
        """Test filtering by Region."""
        params = {"region": [self.dev01.site.region]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {"region_id": [self.dev01.site.region.id]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_site(self):
        """Test filtering by Site."""
        params = {"site": [self.dev01.site.slug]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {"site_id": [self.dev01.site.id]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_tenant(self):
        """Test filtering by Tenant."""
        params = {"tenant": [self.dev01.tenant.slug]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {"tenant_id": [self.dev01.tenant.id]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_tenant_group(self):
        """Test filtering by Tenant Group."""
        params = {"tenant_group": [self.dev01.tenant.group.slug]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {"tenant_group_id": [self.dev01.tenant.group.id]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_rack(self):
        """Test filtering by Rack."""
        params = {"rack": [self.dev01.rack.name]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {"rack_id": [self.dev01.rack.id]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_rack_group(self):
        """Test filtering by Rack Group."""
        params = {"rack_group": [self.dev01.rack.group.slug]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {"rack_group_id": [self.dev01.rack.group.id]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_role(self):
        """Test filtering by Role."""
        params = {"role": [self.dev01.device_role.slug]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {"role_id": [self.dev01.device_role.id]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_platform(self):
        """Test filtering by Platform."""
        params = {"platform": [self.dev01.platform.slug]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {"platform_id": [self.dev01.platform.id]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_manufacturer(self):
        """Test filtering by Manufacturer."""
        params = {"manufacturer": [self.dev01.device_type.manufacturer.slug]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {"manufacturer_id": [self.dev01.device_type.manufacturer.id]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_device_type(self):
        """Test filtering by Device Type."""
        params = {"device_type": [self.dev01.device_type.slug]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {"device_type_id": [self.dev01.device_type.id]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    @skip("Update Status filtering")
    def test_device_status(self):
        """Test filtering by Device Status."""
        params = {"device_status": [self.dev01.status.slug]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {"device_status_id": [self.dev01.status.id]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)


class GoldenConfigModelTestCase(ConfigComplianceModelTestCase):
    """Test filtering operations for GoldenConfig Model."""

    queryset = models.GoldenConfig.objects.all()
    filterset = filters.GoldenConfigFilterSet

    def setUp(self):
        """Set up base objects."""
        create_device_data()
        self.dev01 = Device.objects.get(name="Device 1")
        dev02 = Device.objects.get(name="Device 2")
        dev03 = Device.objects.get(name="Device 3")
        dev04 = Device.objects.get(name="Device 4")

        updates = [self.dev01, dev02, dev03, dev04]
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
        self.platform1 = Platform.objects.create(name="Platform 1", slug="platform-1")
        platform2 = Platform.objects.create(name="Platform 2", slug="platform-2")
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
        params = {"id": self.queryset.values_list("pk", flat=True)[0]}
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
        params = {"platform": [self.platform1]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {"platform_id": [self.platform1.id]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)


class ConfigReplaceModelTestCase(ConfigRemoveModelTestCase):
    """Test filtering operations for ConfigReplace Model."""

    queryset = models.ConfigReplace.objects.all()
    filterset = filters.ConfigReplaceFilterSet

    def setUp(self):
        """Setup Object."""
        self.platform1 = Platform.objects.create(name="Platform 1", slug="platform-1")
        platform2 = Platform.objects.create(name="Platform 2", slug="platform-2")
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
        self.platform1 = Platform.objects.create(name="Platform 1", slug="platform-1")
        platform2 = Platform.objects.create(name="Platform 2", slug="platform-2")
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
        params = {"id": self.queryset.values_list("pk", flat=True)[0]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_name(self):
        """Test filtering by Name."""
        params = {"name": self.obj1.name}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_search(self):
        """Test filtering by Q search value."""
        params = {"q": self.obj1.name[-1:]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
