"""
Management command to populate sample ConfigCompliance data.

Usage:
    python manage.py populate_compliance_data
    python manage.py populate_compliance_data --compliance-rate 0.75
    python manage.py populate_compliance_data --devices 50 --create-missing
    python manage.py populate_compliance_data --clear
"""

import random

from django.core.management.base import BaseCommand
from django.db import transaction
from nautobot.dcim.models import Device, Platform

from nautobot_golden_config.models import (
    ComplianceFeature,
    ComplianceRule,
    ConfigCompliance,
)

SAMPLE_FEATURES = [
    {"name": "NTP", "slug": "ntp"},
    {"name": "BGP", "slug": "bgp"},
    {"name": "OSPF", "slug": "ospf"},
    {"name": "AAA", "slug": "aaa"},
    {"name": "Logging", "slug": "logging"},
    {"name": "SNMP", "slug": "snmp"},
    {"name": "Banner", "slug": "banner"},
    {"name": "DNS", "slug": "dns"},
    {"name": "ACL", "slug": "acl"},
    {"name": "STP", "slug": "stp"},
]

SAMPLE_ACTUAL_CONFIGS = {
    "ntp": "ntp server 10.0.0.1\nntp server 10.0.0.2",
    "bgp": "router bgp 65000\n neighbor 10.1.1.1 remote-as 65001",
    "ospf": "router ospf 1\n network 10.0.0.0 0.255.255.255 area 0",
    "aaa": "aaa new-model\naaa authentication login default local",
    "logging": "logging host 10.0.0.100\nlogging trap informational",
    "snmp": "snmp-server community public RO\nsnmp-server host 10.0.0.200",
    "banner": "banner motd ^Authorized Access Only^",
    "dns": "ip domain-name example.com\nip name-server 8.8.8.8",
    "acl": "ip access-list standard MGMT\n permit 10.0.0.0 0.0.0.255",
    "stp": "spanning-tree mode rapid-pvst\nspanning-tree portfast default",
}

SAMPLE_INTENDED_CONFIGS = {
    "ntp": "ntp server 10.0.0.1\nntp server 10.0.0.2\nntp server 10.0.0.3",
    "bgp": "router bgp 65000\n neighbor 10.1.1.1 remote-as 65001\n neighbor 10.1.1.2 remote-as 65002",
    "ospf": "router ospf 1\n network 10.0.0.0 0.255.255.255 area 0",
    "aaa": "aaa new-model\naaa authentication login default local\naaa authorization exec default local",
    "logging": "logging host 10.0.0.100\nlogging trap informational\nlogging source-interface Loopback0",
    "snmp": "snmp-server community public RO\nsnmp-server host 10.0.0.200",
    "banner": "banner motd ^Authorized Access Only^",
    "dns": "ip domain-name example.com\nip name-server 8.8.8.8\nip name-server 8.8.4.4",
    "acl": "ip access-list standard MGMT\n permit 10.0.0.0 0.0.0.255\n deny any log",
    "stp": "spanning-tree mode rapid-pvst\nspanning-tree portfast default",
}


class Command(BaseCommand):
    """Management command to populate sample ConfigCompliance data for testing."""

    help = "Populate sample ConfigCompliance data across all devices and features for performance testing."

    def add_arguments(self, parser):
        """Add command-line arguments for customizing the data population."""
        parser.add_argument(
            "--compliance-rate",
            type=float,
            default=0.7,
            help="Fraction of records that will be marked compliant (0.0 - 1.0). Default: 0.7",
        )
        parser.add_argument(
            "--create-missing",
            action="store_true",
            default=False,
            help="Create sample ComplianceFeatures and ComplianceRules if none exist.",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            default=False,
            help="Delete all existing ConfigCompliance records before populating.",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=500,
            help="Number of records to bulk-insert per batch. Default: 500",
        )

    def handle(self, *args, **options):
        """Handle the command execution."""
        compliance_rate = options["compliance_rate"]
        create_missing = options["create_missing"]
        clear = options["clear"]
        batch_size = options["batch_size"]

        if not 0.0 <= compliance_rate <= 1.0:
            self.stderr.write("--compliance-rate must be between 0.0 and 1.0")
            return

        if clear:
            deleted, _ = ConfigCompliance.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"Cleared {deleted} existing ConfigCompliance records."))

        # Optionally seed features and rules if the DB is empty
        if create_missing:
            self._create_sample_features_and_rules()

        devices = list(Device.objects.all())
        if not devices:
            self.stderr.write(
                self.style.ERROR("No devices found. Add devices to the database first, then re-run this command.")
            )
            return

        # Build a mapping of platform -> [rules] so we only assign rules valid for a device's platform
        rules_by_platform = {}
        for rule in ComplianceRule.objects.select_related("feature", "platform").all():
            rules_by_platform.setdefault(rule.platform_id, []).append(rule)

        if not rules_by_platform:
            self.stderr.write(
                self.style.ERROR("No ComplianceRules found. Run with --create-missing or create rules manually first.")
            )
            return

        # Gather existing (device_id, rule_id) pairs to avoid unique constraint violations
        existing = set(ConfigCompliance.objects.values_list("device_id", "rule_id"))

        self.stdout.write(f"Found {len(devices)} devices. Building compliance records...")

        to_create = []
        skipped = 0

        for device in devices:
            platform_id = device.platform_id
            rules = rules_by_platform.get(platform_id, [])

            if not rules:
                # Fall back to all rules if device has no platform or no platform-specific rules
                rules = [r for rules_list in rules_by_platform.values() for r in rules_list]

            for rule in rules:
                if (device.pk, rule.pk) in existing:
                    skipped += 1
                    continue

                is_compliant = random.random() < compliance_rate  # noqa: S311
                slug = rule.feature.slug

                actual = SAMPLE_ACTUAL_CONFIGS.get(slug, f"! actual config for {slug}")
                intended = SAMPLE_INTENDED_CONFIGS.get(slug, f"! intended config for {slug}")

                if is_compliant:
                    missing_config = {}
                    extra_config = {}
                    remediation_config = {}
                else:
                    # Simulate a diff for non-compliant records
                    missing_config = {"missing": intended.split("\n")[-1]}
                    extra_config = {"extra": "unexpected config line"}
                    remediation_config = {"remediation": f"no {slug}"}

                to_create.append(
                    ConfigCompliance(
                        device=device,
                        rule=rule,
                        compliance=is_compliant,
                        compliance_int=1 if is_compliant else 0,
                        actual=actual,
                        intended=intended,
                        missing=missing_config,
                        extra=extra_config,
                        remediation=remediation_config,
                        ordered=rule.config_ordered,
                    )
                )

            # Flush batch
            if len(to_create) >= batch_size:
                self._bulk_insert(to_create)
                to_create = []

        # Insert any remaining records
        if to_create:
            self._bulk_insert(to_create)

        total_created = ConfigCompliance.objects.count()
        self.stdout.write(
            self.style.SUCCESS(
                f"Done. Skipped {skipped} existing records. " f"Total ConfigCompliance records in DB: {total_created}"
            )
        )

    def _bulk_insert(self, records):
        with transaction.atomic():
            ConfigCompliance.objects.bulk_create(records, ignore_conflicts=True)
        self.stdout.write(f"  Inserted batch of {len(records)} records.")

    def _create_sample_features_and_rules(self):
        """Create sample ComplianceFeatures and one ComplianceRule per feature per Platform."""
        platforms = list(Platform.objects.all())
        if not platforms:
            self.stderr.write(self.style.WARNING("No platforms found — skipping rule creation. Add platforms first."))
            return

        features_created = 0
        rules_created = 0

        for feature_data in SAMPLE_FEATURES:
            feature, created = ComplianceFeature.objects.get_or_create(
                slug=feature_data["slug"],
                defaults={"name": feature_data["name"], "description": f"Sample {feature_data['name']} feature"},
            )
            if created:
                features_created += 1

            for platform in platforms:
                _, created = ComplianceRule.objects.get_or_create(
                    feature=feature,
                    platform=platform,
                    defaults={
                        "description": f"Sample {feature.name} rule for {platform.name}",
                        "match_config": feature_data["slug"],
                        "config_ordered": False,
                        "custom_compliance": False,
                    },
                )
                if created:
                    rules_created += 1

        self.stdout.write(self.style.SUCCESS(f"Created {features_created} features and {rules_created} rules."))
