"""Params for testing."""

from datetime import datetime, timezone

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.utils.text import slugify
from nautobot.dcim.models import Device, DeviceType, Location, LocationType, Manufacturer, Platform, Rack, RackGroup
from nautobot.extras.choices import JobResultStatusChoices
from nautobot.extras.datasources.registry import get_datasource_contents
from nautobot.extras.models import DynamicGroup, GitRepository, GraphQLQuery, JobResult, Role, Status, Tag
from nautobot.tenancy.models import Tenant, TenantGroup

from nautobot_golden_config.choices import ComplianceRuleConfigTypeChoice
from nautobot_golden_config.models import ComplianceFeature, ComplianceRule, ConfigCompliance, GoldenConfigSetting

User = get_user_model()


def create_device_data():  # pylint: disable=too-many-locals
    """Creates a Device and associated data."""
    ct_device = ContentType.objects.get_for_model(Device)

    manufacturers = (
        Manufacturer.objects.create(name="Manufacturer 1"),
        Manufacturer.objects.create(name="Manufacturer 2"),
        Manufacturer.objects.create(name="Manufacturer 3"),
    )

    device_types = (
        DeviceType.objects.create(
            manufacturer=manufacturers[0],
            model="Model 1",
            is_full_depth=True,
        ),
        DeviceType.objects.create(
            manufacturer=manufacturers[1],
            model="Model 2",
            is_full_depth=True,
        ),
        DeviceType.objects.create(
            manufacturer=manufacturers[2],
            model="Model 3",
            is_full_depth=False,
        ),
    )

    role1 = Role.objects.create(name="Device Role 1")
    role1.content_types.set([ct_device])
    role2 = Role.objects.create(name="Device Role 2")
    role2.content_types.set([ct_device])
    role3 = Role.objects.create(name="Device Role 3")
    role3.content_types.set([ct_device])
    device_roles = (role1, role2, role3)

    device_statuses = Status.objects.get_for_model(Device)
    device_status_map = {ds.name: ds for ds in device_statuses.all()}

    platforms = (
        Platform.objects.create(name="Platform 1"),
        Platform.objects.create(name="Platform 2"),
        Platform.objects.create(name="Platform 3"),
    )

    lt_region = LocationType.objects.create(name="Region")
    lt_site = LocationType.objects.create(name="Site", parent=lt_region)
    lt_site.content_types.set([ct_device])

    regions = (
        Location.objects.create(name="Region 1", location_type=lt_region, status=device_status_map["Active"]),
        Location.objects.create(name="Region 2", location_type=lt_region, status=device_status_map["Active"]),
        Location.objects.create(name="Region 3", location_type=lt_region, status=device_status_map["Active"]),
    )

    sites = (
        Location.objects.create(
            name="Site 1", location_type=lt_site, parent=regions[0], status=device_status_map["Active"]
        ),
        Location.objects.create(
            name="Site 2", location_type=lt_site, parent=regions[1], status=device_status_map["Active"]
        ),
        Location.objects.create(
            name="Site 3", location_type=lt_site, parent=regions[2], status=device_status_map["Active"]
        ),
        Location.objects.create(
            name="Site 1", location_type=lt_site, parent=regions[2], status=device_status_map["Active"]
        ),
    )

    rack_group_parent = RackGroup.objects.create(name="Rack Group Parent", location=sites[0])

    rack_groups = (
        RackGroup.objects.create(name="Rack Group 1", location=sites[0], parent=rack_group_parent),
        RackGroup.objects.create(name="Rack Group 2", location=sites[1]),
        RackGroup.objects.create(name="Rack Group 3", location=sites[2]),
        RackGroup.objects.create(name="Rack Group 4", location=sites[0], parent=rack_group_parent),
        RackGroup.objects.create(name="Rack Group 1", location=sites[3]),
    )

    racks = (
        Rack.objects.create(
            name="Rack 1", location=sites[0], rack_group=rack_groups[0], status=device_status_map["Active"]
        ),
        Rack.objects.create(
            name="Rack 2", location=sites[1], rack_group=rack_groups[1], status=device_status_map["Active"]
        ),
        Rack.objects.create(
            name="Rack 3", location=sites[2], rack_group=rack_groups[2], status=device_status_map["Active"]
        ),
        Rack.objects.create(
            name="Rack 4", location=sites[0], rack_group=rack_groups[3], status=device_status_map["Active"]
        ),
        Rack.objects.create(
            name="Rack 5", location=sites[3], rack_group=rack_groups[4], status=device_status_map["Active"]
        ),
    )

    tenant_group_parent = TenantGroup.objects.create(name="Tenant group parent")

    tenant_groups = (
        TenantGroup.objects.create(name="Tenant group 1", parent=tenant_group_parent),
        TenantGroup.objects.create(name="Tenant group 2"),
        TenantGroup.objects.create(name="Tenant group 3", parent=tenant_group_parent),
    )

    tenants = (
        Tenant.objects.create(name="Tenant 1", tenant_group=tenant_groups[0]),
        Tenant.objects.create(name="Tenant 2", tenant_group=tenant_groups[1]),
        Tenant.objects.create(name="Tenant 3", tenant_group=tenant_groups[2]),
    )

    Device.objects.create(
        name="Device 1",
        device_type=device_types[0],
        role=device_roles[0],
        platform=platforms[0],
        tenant=tenants[0],
        location=sites[0],
        rack=racks[0],
        status=device_status_map["Active"],
    )
    Device.objects.create(
        name="Device 2",
        device_type=device_types[1],
        role=device_roles[1],
        platform=platforms[1],
        tenant=tenants[1],
        location=sites[1],
        rack=racks[1],
        status=device_status_map["Staged"],
    )
    Device.objects.create(
        name="Device 3",
        device_type=device_types[2],
        role=device_roles[2],
        platform=platforms[2],
        tenant=tenants[2],
        location=sites[2],
        rack=racks[2],
        status=device_status_map["Failed"],
    )
    Device.objects.create(
        name="Device 4",
        device_type=device_types[0],
        role=device_roles[0],
        platform=platforms[0],
        tenant=tenants[0],
        location=sites[0],
        rack=racks[0],
        status=device_status_map["Active"],
    )
    Device.objects.create(
        name="Device 5",
        device_type=device_types[0],
        role=device_roles[0],
        platform=platforms[0],
        tenant=tenants[0],
        location=sites[3],
        rack=racks[4],
        status=device_status_map["Active"],
    )
    Device.objects.create(
        name="Device 6",
        device_type=device_types[0],
        role=device_roles[0],
        platform=platforms[0],
        tenant=tenants[0],
        location=sites[0],
        rack=racks[3],
        status=device_status_map["Active"],
    )


def create_device(name="foobaz"):
    """Creates a Device to be used with tests."""
    ct_device = ContentType.objects.get_for_model(Device)
    status, _ = Status.objects.get_or_create(name="Failed")
    lt_region, _ = LocationType.objects.get_or_create(name="Region", nestable=True)
    lt_site, _ = LocationType.objects.get_or_create(name="Site", parent=lt_region)
    lt_site.content_types.set([ct_device])
    parent_region, _ = Location.objects.get_or_create(name="Parent Region 1", location_type=lt_region, status=status)
    child_region, _ = Location.objects.get_or_create(
        name="Child Region 1", parent=parent_region, location_type=lt_region, status=status
    )
    site, _ = Location.objects.get_or_create(name="Site 1", parent=child_region, location_type=lt_site, status=status)
    manufacturer, _ = Manufacturer.objects.get_or_create(name="Manufacturer")
    device_role, _ = Role.objects.get_or_create(name="Role 1")
    device_role.content_types.set([ct_device])
    device_type, _ = DeviceType.objects.get_or_create(manufacturer=manufacturer, model="Device Type 1")
    platform, _ = Platform.objects.get_or_create(
        manufacturer=manufacturer, name="Platform 1", network_driver="cisco_ios"
    )
    device = Device.objects.create(
        name=name, platform=platform, location=site, role=device_role, device_type=device_type, status=status
    )
    return device


def create_orphan_device(name="orphan"):
    """Creates a Device to be used with tests."""
    ct_device = ContentType.objects.get_for_model(Device)
    status, _ = Status.objects.get_or_create(name="Offline")
    lt_region, _ = LocationType.objects.get_or_create(name="Region", nestable=True)
    lt_site, _ = LocationType.objects.get_or_create(name="Site", parent=lt_region)
    lt_site.content_types.set([ct_device])
    parent_region, _ = Location.objects.get_or_create(name="Parent Region 4", location_type=lt_region, status=status)
    child_region, _ = Location.objects.get_or_create(
        name="Child Region 4", parent=parent_region, location_type=lt_region, status=status
    )
    site, _ = Location.objects.get_or_create(name="Site 4", parent=child_region, location_type=lt_site, status=status)
    manufacturer, _ = Manufacturer.objects.get_or_create(name="Manufacturer 4")
    device_role, _ = Role.objects.get_or_create(name="Role 4")
    device_type, _ = DeviceType.objects.get_or_create(manufacturer=manufacturer, model="Device Type 4")
    platform, _ = Platform.objects.get_or_create(
        manufacturer=manufacturer, name="Platform 4", network_driver="cisco_ios"
    )
    tag, _ = Tag.objects.get_or_create(name="Orphaned")
    tag.content_types.add(ct_device)
    device = Device.objects.create(
        name=name, platform=platform, location=site, role=device_role, device_type=device_type, status=status
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


def create_feature_rule_xml(device, feature="foo4", rule="xml"):
    """Creates a Feature/Rule Mapping and Returns the rule."""
    feature_obj, _ = ComplianceFeature.objects.get_or_create(slug=feature, name=feature)
    rule = ComplianceRule(
        feature=feature_obj,
        platform=device.platform,
        config_type=ComplianceRuleConfigTypeChoice.TYPE_XML,
        config_ordered=False,
    )
    rule.save()
    return rule


def create_feature_rule_xml_with_remediation(device, feature="foo5", rule="xml"):
    """Creates a Feature/Rule Mapping with remediation enabled and Returns the rule."""
    feature_obj, _ = ComplianceFeature.objects.get_or_create(slug=feature, name=feature)
    rule = ComplianceRule(
        feature=feature_obj,
        platform=device.platform,
        config_type=ComplianceRuleConfigTypeChoice.TYPE_XML,
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
        remediation={"a": "b"},
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
        provided_contents=[
            entry.content_identifier
            for entry in get_datasource_contents("extras.gitrepository")
            if entry.content_identifier == provides
        ],
    )
    git_repo_1.save()

    name = "test-backup-repo-2"
    provides = "nautobot_golden_config.backupconfigs"
    git_repo_2 = GitRepository(
        name=name,
        slug=slugify(name),
        remote_url=f"http://www.remote-repo.com/{name}.git",
        branch="main",
        provided_contents=[
            entry.content_identifier
            for entry in get_datasource_contents("extras.gitrepository")
            if entry.content_identifier == provides
        ],
    )
    git_repo_2.save()

    name = "test-intended-repo-1"
    provides = "nautobot_golden_config.intendedconfigs"
    git_repo_3 = GitRepository(
        name=name,
        slug=slugify(name),
        remote_url=f"http://www.remote-repo.com/{name}.git",
        branch="main",
        provided_contents=[
            entry.content_identifier
            for entry in get_datasource_contents("extras.gitrepository")
            if entry.content_identifier == provides
        ],
    )
    git_repo_3.save()

    name = "test-intended-repo-2"
    provides = "nautobot_golden_config.intendedconfigs"
    git_repo_4 = GitRepository(
        name=name,
        slug=slugify(name),
        remote_url=f"http://www.remote-repo.com/{name}.git",
        branch="main",
        provided_contents=[
            entry.content_identifier
            for entry in get_datasource_contents("extras.gitrepository")
            if entry.content_identifier == provides
        ],
    )
    git_repo_4.save()

    name = "test-jinja-repo-1"
    provides = "nautobot_golden_config.jinjatemplate"
    git_repo_5 = GitRepository(
        name=name,
        slug=slugify(name),
        remote_url=f"http://www.remote-repo.com/{name}.git",
        branch="main",
        provided_contents=[
            entry.content_identifier
            for entry in get_datasource_contents("extras.gitrepository")
            if entry.content_identifier == provides
        ],
    )
    git_repo_5.save()


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
        provided_contents=[
            entry.content_identifier
            for entry in get_datasource_contents("extras.gitrepository")
            if entry.content_identifier == content_provides
        ],
    )
    git_repo.save()


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
        variables=variables,
        query=query,
    )
    saved_query_1.save()

    name = "GC-SoTAgg-Query-2"
    query = """query ($device_id: ID!) {
                  device(id: $device_id) {
                    config_context
                    name
                    location {
                      name
                    }
                  }
               }
            """
    saved_query_2 = GraphQLQuery(
        name=name,
        variables=variables,
        query=query,
    )
    saved_query_2.save()

    name = "GC-SoTAgg-Query-3"
    query = '{devices(name:"ams-edge-01"){id}}'
    saved_query_3 = GraphQLQuery(
        name=name,
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
        query=query,
    )
    saved_query_5.save()


def create_job_result() -> None:
    """Create a JobResult and return the object."""
    user, _ = User.objects.get_or_create(username="testuser")
    result = JobResult.objects.create(
        name="Test-Job-Result",
        task_name="Test-Job-Result-Task-Name",
        worker="celery",
        user=user,
    )
    result.status = JobResultStatusChoices.STATUS_SUCCESS
    result.completed = datetime.now(timezone.utc)
    result.validated_save()
    return result


def dgs_gc_settings_and_job_repo_objects():
    """Create Multiple DGS GC settings and other objects."""
    create_git_repos()
    create_saved_queries()
    # Since we enforce a singleton pattern on this model, nuke the auto-created object.
    GoldenConfigSetting.objects.all().delete()

    dynamic_group1 = DynamicGroup.objects.create(
        name="dg foobaz",
        content_type=ContentType.objects.get_for_model(Device),
        filter={"platform": ["Platform 1"]},
    )
    dynamic_group2 = DynamicGroup.objects.create(
        name="dg foobaz2",
        content_type=ContentType.objects.get_for_model(Device),
        filter={"platform": ["Platform 4"]},
    )

    GoldenConfigSetting.objects.create(
        name="test_name",
        slug="test_slug",
        weight=1000,
        description="Test Description.",
        backup_path_template="test/backup",
        intended_path_template="test/intended",
        jinja_path_template="{{jinja_path}}",
        backup_test_connectivity=True,
        dynamic_group=dynamic_group1,
        sot_agg_query=GraphQLQuery.objects.get(name="GC-SoTAgg-Query-1"),
        backup_repository=GitRepository.objects.get(name="test-backup-repo-1"),
        intended_repository=GitRepository.objects.get(name="test-intended-repo-1"),
        jinja_repository=GitRepository.objects.get(name="test-jinja-repo-1"),
    )
    GoldenConfigSetting.objects.create(
        name="test_name2",
        slug="test_slug2",
        weight=1000,
        description="Test Description.",
        backup_path_template="test/backup",
        intended_path_template="test/intended",
        jinja_path_template="{{jinja_path}}",
        backup_test_connectivity=True,
        dynamic_group=dynamic_group2,
        sot_agg_query=GraphQLQuery.objects.get(name="GC-SoTAgg-Query-1"),
        backup_repository=GitRepository.objects.get(name="test-backup-repo-2"),
        intended_repository=GitRepository.objects.get(name="test-intended-repo-2"),
        jinja_repository=GitRepository.objects.get(name="test-jinja-repo-1"),
    )
