"""Generate test data for the Golden Config app."""

import random

from django.core.management.base import BaseCommand
from django.db import DEFAULT_DB_ALIAS
from nautobot.core.factory import get_random_instances
from nautobot.dcim.models import Platform
from netutils.lib_mapper import NETUTILSPARSER_LIB_MAPPER_REVERSE

from nautobot_golden_config.models import (
    ComplianceFeature,
    ComplianceRule,
    ConfigCompliance,
    GoldenConfig,
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

        # TODO: Create ConfigRemoves
        # TODO: Create ConfigReplaces
        # TODO: Create RemediationSettings
        # TODO: Create ConfigPlans

    def handle(self, *args, **options):
        """Entry point to the management command."""
        self._generate_static_data(db=options["database"])

        self.stdout.write(self.style.SUCCESS(f"Database {options['database']} populated with app data successfully!"))
