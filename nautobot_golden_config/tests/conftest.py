"""Params for testing."""
from datetime import datetime
import uuid
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.utils.text import slugify
from nautobot.dcim.models import Device, DeviceRole, DeviceType, Manufacturer, Platform, Rack, RackGroup, Region, Site
from nautobot.extras.datasources.registry import get_datasource_contents
from nautobot.extras.models import GitRepository, GraphQLQuery, Status, Tag, JobResult
from nautobot.tenancy.models import Tenant, TenantGroup
import pytz
from nautobot_golden_config.choices import ComplianceRuleConfigTypeChoice
from nautobot_golden_config.models import ComplianceFeature, ComplianceRule, ConfigCompliance


User = get_user_model()


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
    status, _ = Status.objects.get_or_create(name="Failed")
    device = Device.objects.create(
        name=name, platform=platform, site=site, device_role=device_role, device_type=device_type, status=status
    )
    return device


def create_orphan_device(name="orphan"):
    """Creates a Device to be used with tests."""
    parent_region, _ = Region.objects.get_or_create(name="Parent Region 4", slug="parent_region-4")
    child_region, _ = Region.objects.get_or_create(name="Child Region 4", slug="child_region-4", parent=parent_region)
    site, _ = Site.objects.get_or_create(name="Site 4", slug="site-4", region=child_region)
    manufacturer, _ = Manufacturer.objects.get_or_create(name="Manufacturer 4", slug="manufacturer-4")
    device_role, _ = DeviceRole.objects.get_or_create(name="Role 4", slug="role-4")
    device_type, _ = DeviceType.objects.get_or_create(
        manufacturer=manufacturer, model="Device Type 4", slug="device-type-4"
    )
    platform, _ = Platform.objects.get_or_create(manufacturer=manufacturer, name="Platform 4", slug="platform-4")
    content_type = ContentType.objects.get(app_label="dcim", model="device")
    tag, _ = Tag.objects.get_or_create(name="Orphaned", slug="orphaned")
    tag.content_types.add(content_type)
    status, _ = Status.objects.get_or_create(name="Offline")
    device = Device.objects.create(
        name=name, platform=platform, site=site, device_role=device_role, device_type=device_type, status=status
    )
    device.tags.add(tag)
    return device


def create_feature_rule_json(device, feature="foo1", rule="json"):
    """Creates a Feature/Rule Mapping and Returns the rule."""
    feature_obj, _ = ComplianceFeature.objects.get_or_create(slug=feature, name=feature)
    rule = ComplianceRule(
        feature=feature_obj,
        platform=device.platform,
        config_type=ComplianceRuleConfigTypeChoice.TYPE_JSON,
        config_ordered=False,
    )
    rule.save()
    return rule


def create_feature_rule_json_with_remediation(device, feature="foo2", rule="json"):
    """Creates a Feature/Rule Mapping with remediation enabled and Returns the rule."""
    feature_obj, _ = ComplianceFeature.objects.get_or_create(slug=feature, name=feature)
    rule = ComplianceRule(
        feature=feature_obj,
        platform=device.platform,
        config_type=ComplianceRuleConfigTypeChoice.TYPE_JSON,
        config_ordered=False,
        config_remediation=True,
    )
    rule.save()
    return rule


def create_feature_rule_cli_with_remediation(device, feature="foo3", rule="cli"):
    """Creates a Feature/Rule Mapping with remediation enabled and Returns the rule."""
    feature_obj, _ = ComplianceFeature.objects.get_or_create(slug=feature, name=feature)
    rule = ComplianceRule(
        feature=feature_obj,
        platform=device.platform,
        config_type=ComplianceRuleConfigTypeChoice.TYPE_CLI,
        config_ordered=False,
        config_remediation=True,
    )
    rule.save()
    return rule


def create_feature_rule_cli(device, feature="foo_cli"):
    """Creates a Feature/Rule Mapping and Returns the rule."""
    feature_obj, _ = ComplianceFeature.objects.get_or_create(slug=feature, name=feature)
    rule, _ = ComplianceRule.objects.get_or_create(
        feature=feature_obj,
        platform=device.platform,
        config_type=ComplianceRuleConfigTypeChoice.TYPE_CLI,
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


# """Fixture Models."""
def create_git_repos() -> None:
    """Create five instances of Git Repos.

    Two GitRepository objects provide Backups.
    Two GitRepository objects provide Intended.
    One GitRepository objects provide Jinja Templates.
    The provided content is matched through a loop, in order to prevent any errors if object ID's change.
    """
    name = "test-backup-repo-1"
    provides = "nautobot_golden_config.backupconfigs"
    git_repo_1 = GitRepository(
        name=name,
        slug=slugify(name),
        remote_url=f"http://www.remote-repo.com/{name}.git",
        branch="main",
        username="CoolDeveloper_1",
        provided_contents=[
            entry.content_identifier
            for entry in get_datasource_contents("extras.gitrepository")
            if entry.content_identifier == provides
        ],
    )
    git_repo_1.save(trigger_resync=False)

    name = "test-backup-repo-2"
    provides = "nautobot_golden_config.backupconfigs"
    git_repo_2 = GitRepository(
        name=name,
        slug=slugify(name),
        remote_url=f"http://www.remote-repo.com/{name}.git",
        branch="main",
        username="CoolDeveloper_1",
        provided_contents=[
            entry.content_identifier
            for entry in get_datasource_contents("extras.gitrepository")
            if entry.content_identifier == provides
        ],
    )
    git_repo_2.save(trigger_resync=False)

    name = "test-intended-repo-1"
    provides = "nautobot_golden_config.intendedconfigs"
    git_repo_3 = GitRepository(
        name=name,
        slug=slugify(name),
        remote_url=f"http://www.remote-repo.com/{name}.git",
        branch="main",
        username="CoolDeveloper_1",
        provided_contents=[
            entry.content_identifier
            for entry in get_datasource_contents("extras.gitrepository")
            if entry.content_identifier == provides
        ],
    )
    git_repo_3.save(trigger_resync=False)

    name = "test-intended-repo-2"
    provides = "nautobot_golden_config.intendedconfigs"
    git_repo_4 = GitRepository(
        name=name,
        slug=slugify(name),
        remote_url=f"http://www.remote-repo.com/{name}.git",
        branch="main",
        username="CoolDeveloper_1",
        provided_contents=[
            entry.content_identifier
            for entry in get_datasource_contents("extras.gitrepository")
            if entry.content_identifier == provides
        ],
    )
    git_repo_4.save(trigger_resync=False)

    name = "test-jinja-repo-1"
    provides = "nautobot_golden_config.jinjatemplate"
    git_repo_5 = GitRepository(
        name=name,
        slug=slugify(name),
        remote_url=f"http://www.remote-repo.com/{name}.git",
        branch="main",
        username="CoolDeveloper_1",
        provided_contents=[
            entry.content_identifier
            for entry in get_datasource_contents("extras.gitrepository")
            if entry.content_identifier == provides
        ],
    )
    git_repo_5.save(trigger_resync=False)


def create_helper_repo(name="foobaz", provides=None):
    """
    Create a backup and/or intended repo to test helper functions.
    """
    content_provides = f"nautobot_golden_config.{provides}"
    git_repo = GitRepository(
        name=name,
        slug=slugify(name),
        remote_url=f"http://www.remote-repo.com/{name}.git",
        branch="main",
        username="CoolDeveloper_1",
        provided_contents=[
            entry.content_identifier
            for entry in get_datasource_contents("extras.gitrepository")
            if entry.content_identifier == content_provides
        ],
    )
    git_repo.save(trigger_resync=False)


def create_saved_queries() -> None:
    """
    Create saved GraphQL queries.
    """
    variables = {"device_id": ""}

    name = "GC-SoTAgg-Query-1"
    query = """query ($device_id: ID!) {
                  device(id: $device_id) {
                    name
                    tenant {
                      name
                    }
                  }
               }
            """
    saved_query_1 = GraphQLQuery(
        name=name,
        slug=slugify(name),
        variables=variables,
        query=query,
    )
    saved_query_1.save()

    name = "GC-SoTAgg-Query-2"
    query = """query ($device_id: ID!) {
                  device(id: $device_id) {
                    config_context
                    name
                    site {
                      name
                    }
                  }
               }
            """
    saved_query_2 = GraphQLQuery(
        name=name,
        slug=slugify(name),
        variables=variables,
        query=query,
    )
    saved_query_2.save()

    name = "GC-SoTAgg-Query-3"
    query = '{devices(name:"ams-edge-01"){id}}'
    saved_query_3 = GraphQLQuery(
        name=name,
        slug=slugify(name),
        query=query,
    )
    saved_query_3.save()

    name = "GC-SoTAgg-Query-4"
    query = """
        query {
            compliance_rules {
                feature {
                  name
                }
                platform {
                    name
                }
                description
                config_ordered
                match_config
            }
        }
    """
    saved_query_4 = GraphQLQuery(
        name=name,
        slug=slugify(name),
        query=query,
    )
    saved_query_4.save()

    name = "GC-SoTAgg-Query-5"
    query = """
        query {
            golden_config_settings {
                name
                slug
                weight
                backup_path_template
                intended_path_template
                jinja_path_template
                backup_test_connectivity
                sot_agg_query {
                    name
                }
            }
        }
    """
    saved_query_5 = GraphQLQuery(
        name=name,
        slug=slugify(name),
        query=query,
    )
    saved_query_5.save()


def create_job_result() -> None:
    """Create a JobResult and return the object."""
    obj_type = ContentType.objects.get(app_label="extras", model="job")
    user, _ = User.objects.get_or_create(username="testuser")
    result = JobResult.objects.create(
        name="Test-Job-Result",
        obj_type=obj_type,
        user=user,
        job_id=uuid.uuid4(),
    )
    result.status = "completed"
    result.completed = datetime.now(pytz.UTC)
    result.validated_save()
    return result
