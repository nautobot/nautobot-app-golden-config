"""Golden Configuration Plugin GraphQL Testing."""

import uuid

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.test.client import RequestFactory

from graphql import get_default_backend
from graphene_django.settings import graphene_settings

from nautobot.dcim.models import Platform, Site, Device, Manufacturer, DeviceRole, DeviceType
from nautobot.extras.models import GitRepository, GraphQLQuery, DynamicGroup

from nautobot_golden_config.models import (
    ComplianceFeature,
    ComplianceRule,
    ConfigCompliance,
    GoldenConfig,
    GoldenConfigSetting,
    ConfigRemove,
    ConfigReplace,
)

from .conftest import create_saved_queries

# Use the proper swappable User model
User = get_user_model()

GIT_DATA = [
    {
        "created": "2021-02-22",
        "last_updated": "2021-02-23T03:32:46.414Z",
        "_custom_field_data": {},
        "name": "backups",
        "slug": "backups",
        "remote_url": "https://github.com/nautobot/demo-gc-backups",
        "branch": "main",
        "current_head": "c87710902da71e24c1b308a5ac12e33292726e4e",
        "username": "",
        "provided_contents": ["nautobot_golden_config.backupconfigs"],
    },
    {
        "created": "2021-02-22",
        "last_updated": "2021-02-23T03:32:46.868Z",
        "_custom_field_data": {},
        "name": "configs",
        "slug": "configs",
        "remote_url": "https://github.com/nautobot/demo-gc-generated-configs",
        "branch": "main",
        "current_head": "e975bbf3054778bf3f2d971e1b8d100a371b417e",
        "username": "",
        "provided_contents": ["nautobot_golden_config.intendedconfigs"],
    },
    {
        "created": "2021-02-22",
        "last_updated": "2021-02-22T05:01:21.863Z",
        "_custom_field_data": {},
        "name": "data",
        "slug": "data",
        "remote_url": "https://github.com/nautobot/demo-git-datasource",
        "branch": "main",
        "current_head": "f18b081ed8ca28fd7c4a8a3e46ef9cf909e29a57",
        "username": "",
        "provided_contents": ["extras.configcontext"],
    },
    {
        "created": "2021-02-22",
        "last_updated": "2021-02-22T05:01:32.046Z",
        "_custom_field_data": {},
        "name": "templates",
        "slug": "templates",
        "remote_url": "https://github.com/nautobot/demo-gc-templates",
        "branch": "main",
        "current_head": "f62171f19e4c743669120363779340b1b188b0dd",
        "username": "",
        "provided_contents": ["nautobot_golden_config.jinjatemplate"],
    },
]


class TestGraphQLQuery(TestCase):  # pylint: disable=too-many-instance-attributes
    """Test GraphQL Queries for Golden Config Plugin."""

    def setUp(self):
        """Setup request and create test data to validate GraphQL."""
        super().setUp()
        self.user = User.objects.create(username="Super User", is_active=True, is_superuser=True)
        create_saved_queries()

        # Initialize fake request that will be required to execute GraphQL query
        self.request = RequestFactory().request(SERVER_NAME="WebRequestContext")
        self.request.id = uuid.uuid4()
        self.request.user = self.user

        self.backend = get_default_backend()
        self.schema = graphene_settings.SCHEMA

        manufacturer = Manufacturer.objects.create(name="Manufacturer 1", slug="manufacturer-1")
        self.devicetype = DeviceType.objects.create(
            manufacturer=manufacturer, model="Device Type 1", slug="device-type-1"
        )
        self.devicerole1 = DeviceRole.objects.create(name="Device Role 1", slug="device-role-1")

        self.site1 = Site.objects.create(name="Site-1", slug="site-1", asn=65000)
        self.platform1 = Platform.objects.create(
            name="Platform1",
            slug="platform1",
        )

        self.device1 = Device.objects.create(
            name="Device 1",
            device_type=self.devicetype,
            device_role=self.devicerole1,
            platform=self.platform1,
            site=self.site1,
            comments="First Device",
        )

        for item in GIT_DATA:
            git_obj = GitRepository.objects.create(**item)
            git_obj.save()

        # Since we enforce a singleton pattern on this model, nuke the auto-created object.
        GoldenConfigSetting.objects.all().delete()

        self.content_type = ContentType.objects.get(app_label="dcim", model="device")

        dynamic_group = DynamicGroup.objects.create(
            name="test1 site site-4",
            slug="test1-site-site-4",
            content_type=self.content_type,
            filter={"platform": ["platform1"]},
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
            dynamic_group=dynamic_group,
            sot_agg_query=GraphQLQuery.objects.get(name="GC-SoTAgg-Query-1"),
            backup_repository=GitRepository.objects.get(
                provided_contents__contains="nautobot_golden_config.backupconfigs"
            ),
            intended_repository=GitRepository.objects.get(
                provided_contents__contains="nautobot_golden_config.intendedconfigs"
            ),
            jinja_repository=GitRepository.objects.get(
                provided_contents__contains="nautobot_golden_config.jinjatemplate"
            ),
        )

        self.feature1 = ComplianceFeature.objects.create(
            name="aaa",
            description="Test Desc",
        )

        self.rule1 = ComplianceRule.objects.create(
            feature=self.feature1,
            platform=self.platform1,
            description="Test Desc",
            config_ordered=True,
            match_config="aaa ",
        )

        ConfigCompliance.objects.create(
            device=self.device1,
            rule=self.rule1,
            compliance=True,
            actual="aaa test",
            intended="aaa test",
            missing="",
            extra="",
            ordered=False,
        )

        GoldenConfig.objects.create(
            device=self.device1,
            backup_config="interface Eth1/1\ndescription test",
            intended_config="interface Ethernet1/1\ndescription test",
            compliance_config="interface Ethernet1/1\ndescription test",
        )

        ConfigRemove.objects.create(
            name="Test Removal", platform=self.platform1, description="Test Desc", regex="^.Test.*"
        )

        ConfigReplace.objects.create(
            name="Test Replace",
            platform=self.platform1,
            description="Test Desc",
            regex="username\\s+(\\S+)",
            replace="<redacted>",
        )

    def execute_query(self, query, variables=None):
        """Function to execute a GraphQL query."""
        document = self.backend.document_from_string(self.schema, query)
        if variables:
            return document.execute(context_value=self.request, variable_values=variables)
        return document.execute(context_value=self.request)

    def test_query_config_compliance(self):
        """Test GraphQL Config Compliance Model."""
        query = """
            query {
                config_compliances {
                    device {
                        name
                    }
                    rule {
                      feature {
                        name
                      }
                    }
                    compliance
                    actual
                    intended
                    missing
                    extra
                    ordered
                    }
                }
        """
        response_data = {
            "config_compliances": [
                {
                    "actual": "aaa test",
                    "compliance": True,
                    "device": {"name": "Device 1"},
                    "extra": "",
                    "rule": {"feature": {"name": "aaa"}},
                    "intended": "aaa test",
                    "missing": "",
                    "ordered": True,
                }
            ]
        }
        result = self.execute_query(query)
        self.assertEqual(result.data, response_data)
        self.assertEqual(len(result.data["config_compliances"]), 1)

    def test_query_golden_config(self):
        """Test Configuration management Model."""
        query = """
            query {
                golden_configs {
                    device {
                        name
                    }
                    backup_config
                    intended_config
                    compliance_config
                    }
                }
        """
        # Need to figure out how to execute a mock Job.
        response_data = {
            "golden_configs": [
                {
                    "device": {"name": "Device 1"},
                    "backup_config": "interface Eth1/1\ndescription test",
                    "intended_config": "interface Ethernet1/1\ndescription test",
                    "compliance_config": "interface Ethernet1/1\ndescription test",
                }
            ]
        }
        result = self.execute_query(query)
        self.assertEqual(result.data, response_data)
        self.assertEqual(len(result.data["golden_configs"]), 1)

    def test_query_compliance_rule(self):
        """Test Configuration Compliance Details Model."""
        query = GraphQLQuery.objects.get(name="GC-SoTAgg-Query-4").query
        response_data = {
            "compliance_rules": [
                {
                    "feature": {"name": "aaa"},
                    "platform": {"name": "Platform1"},
                    "description": "Test Desc",
                    "config_ordered": True,
                    "match_config": "aaa ",
                }
            ]
        }
        result = self.execute_query(query)
        self.assertEqual(result.data, response_data)
        self.assertEqual(len(result.data["compliance_rules"]), 1)

    def test_query_golden_config_setting(self):
        """Test GraphQL Golden Config Settings Model."""
        query = GraphQLQuery.objects.get(name="GC-SoTAgg-Query-5").query
        response_data = {
            "golden_config_settings": [
                {
                    "name": "test_name",
                    "slug": "test_slug",
                    "weight": 1000,
                    "backup_path_template": "test/backup",
                    "intended_path_template": "test/intended",
                    "jinja_path_template": "{{jinja_path}}",
                    "backup_test_connectivity": True,
                    "sot_agg_query": {"name": "GC-SoTAgg-Query-1"},
                }
            ]
        }
        result = self.execute_query(query)
        self.assertEqual(result.data, response_data)
        self.assertEqual(len(result.data["golden_config_settings"]), 1)

    def test_query_line_removal(self):
        """Test Regex Line Removal."""
        query = """
            query {
                config_removes {
                    name
                    platform {
                        name
                    }
                    description
                    regex
                }
            }
        """

        response_data = {
            "config_removes": [
                {
                    "name": "Test Removal",
                    "platform": {"name": "Platform1"},
                    "description": "Test Desc",
                    "regex": "^.Test.*",
                }
            ]
        }
        result = self.execute_query(query)
        self.assertEqual(len(result.data["config_removes"]), 1)
        self.assertEqual(result.data, response_data)

    def test_query_line_replace(self):
        """Test Line Replacement Model."""
        query = """
            query {
                config_replaces {
                    name
                    platform {
                        name
                    }
                    description
                    regex
                    replace
                }
            }
        """

        response_data = {
            "config_replaces": [
                {
                    "name": "Test Replace",
                    "platform": {"name": "Platform1"},
                    "description": "Test Desc",
                    "regex": "username\\s+(\\S+)",
                    "replace": "<redacted>",
                }
            ]
        }
        result = self.execute_query(query)
        self.assertEqual(len(result.data["config_replaces"]), 1)
        self.assertEqual(result.data, response_data)
