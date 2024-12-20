"""Generate test data for the Golden Config app."""

import random

from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.db import DEFAULT_DB_ALIAS
from nautobot.core.factory import get_random_instances
from nautobot.dcim.models import Platform
from nautobot.extras.models import DynamicGroup, GraphQLQuery
from netutils.lib_mapper import NETUTILSPARSER_LIB_MAPPER_REVERSE

from nautobot_golden_config.models import (
    ComplianceFeature,
    ComplianceRule,
    ConfigCompliance,
    GoldenConfig,
    GoldenConfigSetting,
)


class Command(BaseCommand):
    """Populate the database with various data as a baseline for testing (automated or manual)."""

    help = __doc__

    def add_arguments(self, parser):  # noqa: D102
        parser.add_argument(
            "--database",
            default=DEFAULT_DB_ALIAS,
            help='The database to generate the test data in. Defaults to the "default" database.',
        )
        parser.add_argument(
            "--flush",
            action="store_true",
            help="Flush any existing golden config data from the database before generating new data.",
        )

    def _generate_static_data(self, db):
        platforms = get_random_instances(
            Platform.objects.using(db).filter(devices__isnull=False).distinct(),
            minimum=2,
            maximum=4,
        )
        devices = [p.devices.first() for p in platforms]

        # Ensure platform has a valid network_driver or compliance generation will fail
        for platform in platforms:
            if platform.network_driver not in NETUTILSPARSER_LIB_MAPPER_REVERSE:
                platform.network_driver = random.choice(list(NETUTILSPARSER_LIB_MAPPER_REVERSE.keys()))  # noqa: S311
                platform.save()

        # Create ComplianceFeatures
        compliance_features = []
        message = "Creating 8 ComplianceFeatures..."
        self.stdout.write(message)
        for i in range(1, 9):
            name = f"ComplianceFeature{i}"
            compliance_features.append(
                ComplianceFeature.objects.using(db).create(
                    name=name, slug=name, description=f"Test ComplianceFeature {i}"
                )
            )

        # Create ComplianceRules
        count = len(compliance_features) * len(platforms)
        message = f"Creating {count} ComplianceRules..."
        self.stdout.write(message)
        for feature in compliance_features:
            for platform in platforms:
                ComplianceRule.objects.using(db).create(
                    feature=feature,
                    platform=platform,
                    description=f"Test ComplianceRule for {feature.name} on {platform.name}",
                    match_config=f"match {feature.name} on {platform.name}",
                )

        # Create ConfigCompliances
        count = len(devices) * len(compliance_features)
        message = f"Creating {count} ConfigCompliances..."
        self.stdout.write(message)
        for device in devices:
            for rule in ComplianceRule.objects.using(db).filter(platform=device.platform):
                is_compliant = random.choice([True, False])  # noqa: S311
                ConfigCompliance.objects.using(db).create(
                    device=device,
                    rule=rule,
                    compliance=is_compliant,
                    compliance_int=int(is_compliant),
                    intended=rule.match_config,
                    actual=rule.match_config if is_compliant else f"mismatch {rule.feature.name}",
                )

        # Create GoldenConfigs
        message = f"Creating {len(devices)} GoldenConfigs..."
        self.stdout.write(message)
        for device in devices:
            GoldenConfig.objects.using(db).create(
                device=device,
                backup_config=f"backup config for {device.name}",
                intended_config=f"intended config for {device.name}",
                compliance_config=f"compliance config for {device.name}",
            )

        # Create GraphQL query for GoldenConfigSetting.sot_agg_query
        message = "Creating test GraphQLQuery for GoldenConfigSetting..."
        self.stdout.write(message)
        graphql_query_variables = {"device_id": ""}
        graphql_sot_agg_query = """
            query ($device_id: ID!) {
              device(id: $device_id) {
                config_context
                hostname: name
                position
                serial
                primary_ip4 {
                  id
                  primary_ip4_for {
                    id
                    name
                  }
                }
                tenant {
                  name
                }
                tags {
                  name
                }
                role {
                  name
                }
                platform {
                  name
                  manufacturer {
                    name
                  }
                  network_driver
                  napalm_driver
                }
                location {
                  name
                  parent {
                    name
                  }
                }
                interfaces {
                  description
                  mac_address
                  enabled
                  name
                  ip_addresses {
                    address
                    tags {
                      id
                    }
                  }
                  connected_circuit_termination {
                    circuit {
                      cid
                      commit_rate
                      provider {
                        name
                      }
                    }
                  }
                  tagged_vlans {
                    id
                  }
                  untagged_vlan {
                    id
                  }
                  cable {
                    termination_a_type
                    status {
                      name
                    }
                    color
                  }
                  tags {
                    id
                  }
                }
              }
            }
        """
        gql_query = GraphQLQuery.objects.using(db).create(
            name="GoldenConfigSetting.sot_agg_query",
            variables=graphql_query_variables,
            query=graphql_sot_agg_query,
        )
        if not GoldenConfigSetting.objects.using(db).exists():
            dynamic_group, _ = DynamicGroup.objects.using(db).get_or_create(
                name="GoldenConfigSetting Dynamic Group",
                defaults={"content_type": ContentType.objects.using(db).get(app_label="dcim", model="device")},
            )
            GoldenConfigSetting.objects.using(db).create(
                name="Default GoldenConfigSetting",
                slug="default_goldenconfigsetting",
                sot_agg_query=gql_query,
                dynamic_group=dynamic_group,
            )
            message = "Creating 1 GoldenConfigSetting..."
            self.stdout.write(message)
        else:
            golden_config_setting = GoldenConfigSetting.objects.first()
            message = f"Applying GraphQLQuery to GoldenConfigSetting '{golden_config_setting.name}'..."
            self.stdout.write(message)
            golden_config_setting.sot_agg_query = gql_query
            golden_config_setting.save()

        # TODO: Create ConfigRemoves
        # TODO: Create ConfigReplaces
        # TODO: Create RemediationSettings
        # TODO: Create ConfigPlans

    def handle(self, *args, **options):
        """Entry point to the management command."""
        if options["flush"]:
            self.stdout.write(self.style.WARNING("Flushing golden config objects from the database..."))
            GoldenConfigSetting.objects.using(options["database"]).all().delete()
            GoldenConfig.objects.using(options["database"]).all().delete()
            ConfigCompliance.objects.using(options["database"]).all().delete()
            ComplianceRule.objects.using(options["database"]).all().delete()
            ComplianceFeature.objects.using(options["database"]).all().delete()
            GraphQLQuery.objects.using(options["database"]).filter(name="GoldenConfigSetting.sot_agg_query").delete()

        self._generate_static_data(db=options["database"])

        self.stdout.write(self.style.SUCCESS(f"Database {options['database']} populated with app data successfully!"))
