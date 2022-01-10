"""Params for testing."""
from nautobot.dcim.models import Device, Site, Manufacturer, DeviceType, DeviceRole, Rack, RackGroup, Region, Platform
from nautobot.tenancy.models import Tenant, TenantGroup
from nautobot.extras.models import Status


from nautobot_golden_config.models import ConfigCompliance, ComplianceFeature, ComplianceRule
from nautobot_golden_config.choices import ComplianceRuleTypeChoice


def create_device_data():
    """Creates a Device and associated data."""
    manufacturers = (
        Manufacturer.objects.create(name="Manufacturer 1", slug="manufacturer-1"),
        Manufacturer.objects.create(name="Manufacturer 2", slug="manufacturer-2"),
        Manufacturer.objects.create(name="Manufacturer 3", slug="manufacturer-3"),
    )

    device_types = (
        DeviceType.objects.create(
            manufacturer=manufacturers[0],
            model="Model 1",
            slug="model-1",
            is_full_depth=True,
        ),
        DeviceType.objects.create(
            manufacturer=manufacturers[1],
            model="Model 2",
            slug="model-2",
            is_full_depth=True,
        ),
        DeviceType.objects.create(
            manufacturer=manufacturers[2],
            model="Model 3",
            slug="model-3",
            is_full_depth=False,
        ),
    )

    device_roles = (
        DeviceRole.objects.create(name="Device Role 1", slug="device-role-1"),
        DeviceRole.objects.create(name="Device Role 2", slug="device-role-2"),
        DeviceRole.objects.create(name="Device Role 3", slug="device-role-3"),
    )

    device_statuses = Status.objects.get_for_model(Device)
    device_status_map = {ds.slug: ds for ds in device_statuses.all()}

    platforms = (
        Platform.objects.create(name="Platform 1", slug="platform-1"),
        Platform.objects.create(name="Platform 2", slug="platform-2"),
        Platform.objects.create(name="Platform 3", slug="platform-3"),
    )

    regions = (
        Region.objects.create(name="Region 1", slug="region-1"),
        Region.objects.create(name="Region 2", slug="region-2"),
        Region.objects.create(name="Region 3", slug="region-3"),
    )

    sites = (
        Site.objects.create(name="Site 1", slug="site-1", region=regions[0]),
        Site.objects.create(name="Site 2", slug="site-2", region=regions[1]),
        Site.objects.create(name="Site 3", slug="site-3", region=regions[2]),
    )

    rack_groups = (
        RackGroup.objects.create(name="Rack Group 1", slug="rack-group-1", site=sites[0]),
        RackGroup.objects.create(name="Rack Group 2", slug="rack-group-2", site=sites[1]),
        RackGroup.objects.create(name="Rack Group 3", slug="rack-group-3", site=sites[2]),
    )

    racks = (
        Rack.objects.create(name="Rack 1", site=sites[0], group=rack_groups[0]),
        Rack.objects.create(name="Rack 2", site=sites[1], group=rack_groups[1]),
        Rack.objects.create(name="Rack 3", site=sites[2], group=rack_groups[2]),
    )

    tenant_groups = (
        TenantGroup.objects.create(name="Tenant group 1", slug="tenant-group-1"),
        TenantGroup.objects.create(name="Tenant group 2", slug="tenant-group-2"),
        TenantGroup.objects.create(name="Tenant group 3", slug="tenant-group-3"),
    )

    tenants = (
        Tenant.objects.create(name="Tenant 1", slug="tenant-1", group=tenant_groups[0]),
        Tenant.objects.create(name="Tenant 2", slug="tenant-2", group=tenant_groups[1]),
        Tenant.objects.create(name="Tenant 3", slug="tenant-3", group=tenant_groups[2]),
    )

    Device.objects.create(
        name="Device 1",
        device_type=device_types[0],
        device_role=device_roles[0],
        platform=platforms[0],
        tenant=tenants[0],
        site=sites[0],
        rack=racks[0],
        status=device_status_map["active"],
    )
    Device.objects.create(
        name="Device 2",
        device_type=device_types[1],
        device_role=device_roles[1],
        platform=platforms[1],
        tenant=tenants[1],
        site=sites[1],
        rack=racks[1],
        status=device_status_map["staged"],
    )
    Device.objects.create(
        name="Device 3",
        device_type=device_types[2],
        device_role=device_roles[2],
        platform=platforms[2],
        tenant=tenants[2],
        site=sites[2],
        rack=racks[2],
        status=device_status_map["failed"],
    )
    Device.objects.create(
        name="Device 4",
        device_type=device_types[0],
        device_role=device_roles[0],
        platform=platforms[0],
        tenant=tenants[0],
        site=sites[0],
        rack=racks[0],
        status=device_status_map["active"],
    )


def create_device(name="foobaz"):
    """Creates a Device to be used with tests."""
    parent_region, _ = Region.objects.get_or_create(name="Parent Region 1", slug="parent_region-1")
    child_region, _ = Region.objects.get_or_create(name="Child Region 1", slug="child_region-1", parent=parent_region)
    site, _ = Site.objects.get_or_create(name="Site 1", slug="site-1", region=child_region)
    manufacturer, _ = Manufacturer.objects.get_or_create(name="Manufacturer 1", slug="manufacturer-1")
    device_role, _ = DeviceRole.objects.get_or_create(name="Role 1", slug="role-1")
    device_type, _ = DeviceType.objects.get_or_create(
        manufacturer=manufacturer, model="Device Type 1", slug="device-type-1"
    )
    platform, _ = Platform.objects.get_or_create(manufacturer=manufacturer, name="Platform 1", slug="platform-1")
    device = Device.objects.create(
        name=name, platform=platform, site=site, device_role=device_role, device_type=device_type
    )
    return device


def create_feature_rule_json(device, feature="foo", rule="json"):
    """Creates a Feature/Rule Mapping and Returns the rule."""
    feature_obj, _ = ComplianceFeature.objects.get_or_create(slug=feature, name=feature)
    rule = ComplianceRule(
        feature=feature_obj,
        platform=device.platform,
        config_type=ComplianceRuleTypeChoice.TYPE_JSON,
        config_ordered=False,
    )
    rule.save()
    return rule


def create_config_compliance(device, compliance_rule=None, actual=None, intended=None):
    """Creates a ConfigCompliance to be used with tests."""
    config_compliance = ConfigCompliance.objects.create(
        device=device,
        rule=compliance_rule,
        actual=actual,
        intended=intended,
    )
    return config_compliance


def create_feature_rule_custom(device, feature="foo", rule="custom"):
    """Creates a Feature/Rule Mapping and Returns the rule."""
    feature_obj, _ = ComplianceFeature.objects.get_or_create(slug=feature, name=feature)
    rule = ComplianceRule(
        feature=feature_obj,
        platform=device.platform,
        config_type=ComplianceRuleTypeChoice.TYPE_CUSTOM,
        config_ordered=False,
    )
    rule.save()
    return rule
