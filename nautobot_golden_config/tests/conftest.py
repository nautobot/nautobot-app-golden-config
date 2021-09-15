"""Params for testing."""
from nautobot.dcim.models import Device, Site, Manufacturer, DeviceType, DeviceRole, Region, Platform

from nautobot_golden_config.models import ConfigCompliance, ComplianceFeature, ComplianceRule
from nautobot_golden_config.choices import ComplianceRuleTypeChoice


def create_device(name="foobaz"):
    """Creates a Device to be used with tests."""
    parent_region, _ = Region.objects.get_or_create(name="Parent Region", slug="parent_region")
    child_region, _ = Region.objects.get_or_create(name="Child Region", slug="child_region", parent=parent_region)
    site, _ = Site.objects.get_or_create(name="foo", slug="foo", region=child_region)
    manufacturer, _ = Manufacturer.objects.get_or_create(name="bar")
    device_role, _ = DeviceRole.objects.get_or_create(name="baz")
    device_type, _ = DeviceType.objects.get_or_create(manufacturer=manufacturer)
    platform, _ = Platform.objects.get_or_create(manufacturer=manufacturer)
    device = Device.objects.create(
        name=name, platform=platform, site=site, device_role=device_role, device_type=device_type
    )
    return device


def create_feature_rule_json(device, feature="foo", rule="json"):
    """Creates a Feature/Rule Mapping and Returns the rule."""
    feature_obj = ComplianceFeature(slug=feature, name=feature)
    feature_obj.save()
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
