"""Unit tests for nautobot_golden_config models."""

from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from nautobot.core.testing import FilterTestCases
from nautobot.dcim.models import Device, Platform
from nautobot.extras.models import Status, Tag

from nautobot_golden_config import filters, models

from .conftest import create_device_data, create_feature_rule_cli, create_feature_rule_json, create_job_result


class ConfigComplianceModelTestCase(TestCase):  # pylint: disable=too-many-public-methods
    """Test filtering operations for ConfigCompliance Model."""

    queryset = models.ConfigCompliance.objects.all()
    filterset = filters.ConfigComplianceFilterSet

    @classmethod
    def setUpTestData(cls):
        """Set up base objects."""
        create_device_data()
        cls.dev01 = Device.objects.get(name="Device 1")
        dev02 = Device.objects.get(name="Device 2")
        cls.dev03 = Device.objects.get(name="Device 3")
        dev04 = Device.objects.get(name="Device 4")
        dev05 = Device.objects.get(name="Device 5")
        dev06 = Device.objects.get(name="Device 6")

        feature_dev01 = create_feature_rule_json(cls.dev01)
        feature_dev02 = create_feature_rule_json(dev02)
        feature_dev03 = create_feature_rule_json(cls.dev03)
        feature_dev05 = create_feature_rule_json(dev05, feature="baz")
        feature_dev06 = create_feature_rule_json(dev06, feature="bar")

        updates = [
            {"device": cls.dev01, "feature": feature_dev01},
            {"device": dev02, "feature": feature_dev02},
            {"device": cls.dev03, "feature": feature_dev03},
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

    @classmethod
    def setUpTestData(cls):
        """Set up base objects."""
        create_device_data()
        cls.dev01 = Device.objects.get(name="Device 1")
        dev02 = Device.objects.get(name="Device 2")
        cls.dev03 = Device.objects.get(name="Device 3")
        dev04 = Device.objects.get(name="Device 4")
        dev05 = Device.objects.get(name="Device 5")
        dev06 = Device.objects.get(name="Device 6")

        updates = [cls.dev01, dev02, cls.dev03, dev04, dev05, dev06]
        for update in updates:
            models.GoldenConfig.objects.create(
                device=update,
            )


class ConfigRemoveModelTestCase(TestCase):
    """Test filtering operations for ConfigRemove Model."""

    queryset = models.ConfigRemove.objects.all()
    filterset = filters.ConfigRemoveFilterSet

    @classmethod
    def setUpTestData(cls):
        """Setup Object."""
        cls.platform1 = Platform.objects.create(name="Platform 1")
        platform2 = Platform.objects.create(name="Platform 2")
        cls.obj1 = models.ConfigRemove.objects.create(
            name="Remove 1", platform=cls.platform1, description="Description 1", regex="^Remove 1"
        )
        models.ConfigRemove.objects.create(
            name="Remove 2", platform=cls.platform1, description="Description 2", regex="^Remove 2"
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

    @classmethod
    def setUpTestData(cls):
        """Setup Object."""
        cls.platform1 = Platform.objects.create(name="Platform 1")
        platform2 = Platform.objects.create(name="Platform 2")
        cls.obj1 = models.ConfigReplace.objects.create(
            name="Remove 1",
            platform=cls.platform1,
            description="Description 1",
            regex="^Remove 1",
            replace="Replace 1",
        )
        models.ConfigReplace.objects.create(
            name="Remove 2",
            platform=cls.platform1,
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

    @classmethod
    def setUpTestData(cls):
        """Setup Object."""
        cls.platform1 = Platform.objects.create(name="Platform 1")
        platform2 = Platform.objects.create(name="Platform 2")
        feature1 = models.ComplianceFeature.objects.create(name="Feature 1", slug="feature-1")
        feature2 = models.ComplianceFeature.objects.create(name="Feature 2", slug="feature-2")
        cls.obj1 = models.ComplianceRule.objects.create(
            platform=cls.platform1, feature=feature1, config_type="cli", config_ordered=True, match_config="config 1"
        )
        models.ComplianceRule.objects.create(
            platform=cls.platform1, feature=feature2, config_type="cli", config_ordered=True, match_config="config 2"
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

    @classmethod
    def setUpTestData(cls):
        """Setup Object."""
        cls.obj1 = models.ComplianceFeature.objects.create(name="Feature 1", slug="feature-1")
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


# pylint: disable=too-many-ancestors
# pylint: disable=too-many-instance-attributes
class ConfigPlanFilterTestCase(FilterTestCases.FilterTestCase):
    """Test filtering operations for ConfigPlan Model."""

    queryset = models.ConfigPlan.objects.all()
    filterset = filters.ConfigPlanFilterSet

    @classmethod
    def setUpTestData(cls):
        """Setup Object."""
        create_device_data()
        cls.device1 = Device.objects.get(name="Device 1")
        cls.device2 = Device.objects.get(name="Device 2")
        cls.rule1 = create_feature_rule_cli(cls.device1, feature="Feature 1")
        cls.feature1 = cls.rule1.feature
        cls.rule2 = create_feature_rule_cli(cls.device2, feature="Feature 2")
        cls.feature2 = cls.rule2.feature
        cls.rule3 = create_feature_rule_cli(cls.device1, feature="Feature 3")
        cls.feature3 = cls.rule3.feature
        cls.status1 = Status.objects.get(name="Not Approved")
        cls.status2 = Status.objects.get(name="Approved")
        cls.tag1, _ = Tag.objects.get_or_create(name="Tag 1")
        cls.tag2, _ = Tag.objects.get_or_create(name="Tag 2")
        cls.tag1.content_types.set([ContentType.objects.get_for_model(models.ConfigPlan)])
        cls.tag2.content_types.set([ContentType.objects.get_for_model(models.ConfigPlan)])
        cls.job_result1 = create_job_result()
        cls.job_result2 = create_job_result()
        cls.config_plan1 = models.ConfigPlan.objects.create(
            device=cls.device1,
            plan_type="intended",
            created="2020-01-01",
            config_set="intended test",
            change_control_id="12345",
            status=cls.status2,
            plan_result_id=cls.job_result1.id,
        )
        cls.config_plan1.tags.add(cls.tag1)
        cls.config_plan1.feature.add(cls.feature1)
        cls.config_plan1.validated_save()
        cls.config_plan2 = models.ConfigPlan.objects.create(
            device=cls.device1,
            plan_type="missing",
            created="2020-01-02",
            config_set="missing test",
            change_control_id="23456",
            status=cls.status1,
            plan_result_id=cls.job_result1.id,
        )
        cls.config_plan2.tags.add(cls.tag2)
        cls.config_plan2.feature.add(cls.feature2)
        cls.config_plan2.validated_save()
        cls.config_plan3 = models.ConfigPlan.objects.create(
            device=cls.device2,
            plan_type="remediation",
            created="2020-01-03",
            config_set="remediation test",
            change_control_id="34567",
            status=cls.status2,
            plan_result_id=cls.job_result2.id,
        )
        cls.config_plan3.tags.add(cls.tag2)
        cls.config_plan3.feature.set([cls.feature1, cls.feature3])
        cls.config_plan3.validated_save()
        cls.config_plan4 = models.ConfigPlan.objects.create(
            device=cls.device2,
            plan_type="manual",
            created="2020-01-04",
            config_set="manual test",
            change_control_id="45678",
            status=cls.status1,
            plan_result_id=cls.job_result1.id,
        )
        cls.config_plan4.tags.add(cls.tag1)
        cls.config_plan4.validated_save()

    def test_full(self):
        """Test without filtering to ensure all have been added."""
        self.assertEqual(self.queryset.count(), 4)

    def test_tags_filter(self):
        self.config_plan1.tags.add(self.tag2)
        self.config_plan1.validated_save()
        super().test_tags_filter()

    def test_search_device_name(self):
        """Test filtering by Q search value."""
        params = {"q": "Device 1"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_search_change_control_id(self):
        """Test filtering by Q search value."""
        params = {"q": "345"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 3)

    def test_filter_device_id(self):
        """Test filtering by Device ID."""
        params = {"device_id": [self.device1.pk]}
        filterset = self.filterset(params, self.queryset)
        self.assertEqual(filterset.qs.count(), 2)
        self.assertQuerysetEqualAndNotEmpty(filterset.qs, self.queryset.filter(device=self.device1).distinct())

    def test_filter_device(self):
        """Test filtering by Device."""
        params = {"device": [self.device1.name]}
        filterset = self.filterset(params, self.queryset)
        self.assertEqual(filterset.qs.count(), 2)
        self.assertQuerysetEqualAndNotEmpty(
            filterset.qs, self.queryset.filter(device__name=self.device1.name).distinct()
        )

    def test_filter_feature_id(self):
        """Test filtering by Feature ID."""
        params = {"feature_id": [self.feature1.pk]}
        filterset = self.filterset(params, self.queryset)
        self.assertEqual(filterset.qs.count(), 2)
        self.assertQuerysetEqualAndNotEmpty(filterset.qs, self.queryset.filter(feature=self.feature1).distinct())

    def test_filter_feature(self):
        """Test filtering by Feature."""
        params = {"feature": [self.feature1.name]}
        filterset = self.filterset(params, self.queryset)
        self.assertEqual(filterset.qs.count(), 2)
        self.assertQuerysetEqualAndNotEmpty(
            filterset.qs, self.queryset.filter(feature__name=self.feature1.name).distinct()
        )

    def test_filter_change_control_id(self):
        """Test filtering by Change Control ID."""
        params = {"change_control_id": self.config_plan1.change_control_id}
        filterset = self.filterset(params, self.queryset)
        self.assertEqual(filterset.qs.count(), 1)
        self.assertQuerysetEqualAndNotEmpty(
            filterset.qs, self.queryset.filter(change_control_id=self.config_plan1.change_control_id).distinct()
        )

    def test_filter_status_id(self):
        """Test filtering by Status ID."""
        params = {"status_id": [self.status1.pk]}
        filterset = self.filterset(params, self.queryset)
        self.assertEqual(filterset.qs.count(), 2)
        self.assertQuerysetEqualAndNotEmpty(filterset.qs, self.queryset.filter(status=self.status1).distinct())

    def test_filter_status(self):
        """Test filtering by Status."""
        params = {"status": [self.status1.name]}
        filterset = self.filterset(params, self.queryset)
        self.assertEqual(filterset.qs.count(), 2)
        self.assertQuerysetEqualAndNotEmpty(
            filterset.qs, self.queryset.filter(status__name=self.status1.name).distinct()
        )

    def test_filter_plan_type(self):
        """Test filtering by Plan Type."""
        params = {"plan_type": [self.config_plan1.plan_type]}
        filterset = self.filterset(params, self.queryset)
        self.assertEqual(filterset.qs.count(), 1)
        self.assertQuerysetEqualAndNotEmpty(
            filterset.qs, self.queryset.filter(plan_type=self.config_plan1.plan_type).distinct()
        )

    def test_filter_tag(self):
        """Test filtering by Tag."""
        params = {"tags": [self.tag1.name]}
        filterset = self.filterset(params, self.queryset)
        self.assertEqual(filterset.qs.count(), 2)
        self.assertQuerysetEqualAndNotEmpty(filterset.qs, self.queryset.filter(tags__name=self.tag1.name).distinct())

    def test_job_result_id(self):
        """Test filtering by Job Result ID."""
        params = {"plan_result_id": [self.job_result1.pk]}
        filterset = self.filterset(params, self.queryset)
        self.assertEqual(filterset.qs.count(), 3)
        self.assertQuerysetEqualAndNotEmpty(
            filterset.qs, self.queryset.filter(plan_result_id=self.job_result1.id).distinct()
        )
