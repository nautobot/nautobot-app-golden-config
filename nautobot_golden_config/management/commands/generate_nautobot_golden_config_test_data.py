"""Generate test data for the Golden Config app."""

import random

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.db import DEFAULT_DB_ALIAS
from nautobot.apps.factory import get_random_instances
from nautobot.dcim.models import Platform
from nautobot.extras.models import DynamicGroup, GraphQLQuery, JobResult, Status
from nautobot.extras.models import Job as JobModel
from nautobot.extras.models.approvals import (
    ApprovalWorkflowDefinition,
    ApprovalWorkflowStageDefinition,
    ApprovalWorkflowStageResponse,
)
from netutils.lib_mapper import NETUTILSPARSER_LIB_MAPPER_REVERSE

from nautobot_golden_config.choices import ConfigPlanTypeChoice
from nautobot_golden_config.jobs import GenerateConfigPlans
from nautobot_golden_config.models import (
    ComplianceFeature,
    ComplianceRule,
    ConfigCompliance,
    ConfigPlan,
    GoldenConfig,
    GoldenConfigSetting,
)

APPROVERS_GROUP_NAME = "Golden Config Test Approvers"
APPROVER_USERNAME = "gc-test-approver"
APPROVAL_DEFINITION_NAME = "Golden Config Test Config Plan Approval"
APPROVAL_SAMPLE_PREFIX = "approval-sample"


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

    def _generate_static_data(self, db):  # pylint: disable=too-many-locals
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
            golden_config_setting = GoldenConfigSetting.objects.using(db).create(
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
        self.stdout.write(f"Creating {len(devices)} ConfigPlans")
        for device in devices:
            job_model = GenerateConfigPlans().job_model
            plan_result = JobResult.objects.create(
                job_model=job_model,
            )
            ConfigPlan.objects.create(
                plan_type=ConfigPlanTypeChoice.TYPE_MANUAL,
                device=device,
                config_set="""hostname foo""",
                plan_result=plan_result,
            )
        self._generate_approval_data(golden_config_setting, devices[0])
        JobModel.objects.using(db).filter(module_name="nautobot_golden_config.jobs").update(
            enabled=True,
        )

    def _generate_approval_data(self, golden_config_setting, device):
        """Create an approval workflow, its approvers, and a sample Config Plan in each approval state."""
        self.stdout.write("Creating Config Plan approval workflow test data...")
        approver, _ = get_user_model().objects.get_or_create(username=APPROVER_USERNAME)
        approvers, _ = Group.objects.get_or_create(name=APPROVERS_GROUP_NAME)
        approvers.user_set.add(approver)
        definition, _ = ApprovalWorkflowDefinition.objects.get_or_create(
            name=APPROVAL_DEFINITION_NAME,
            defaults={"model_content_type": ContentType.objects.get_for_model(ConfigPlan), "weight": 100},
        )
        ApprovalWorkflowStageDefinition.objects.get_or_create(
            approval_workflow_definition=definition,
            name="Network review",
            defaults={"sequence": 10, "min_approvers": 1, "approver_group": approvers},
        )
        job_model = GenerateConfigPlans().job_model

        def create_sample_plan(plan_type, label, status=None):
            return ConfigPlan.objects.create(
                plan_type=plan_type,
                device=device,
                config_set=f"hostname {device.name}\n! approval sample: {label}",
                change_control_id=f"{APPROVAL_SAMPLE_PREFIX}-{label}",
                plan_result=JobResult.objects.create(job_model=job_model, user=approver),
                status=status,
            )

        def respond(plan, state, comments):
            ApprovalWorkflowStageResponse.objects.create(
                approval_workflow_stage=plan.approval_workflow.approval_workflow_stages.get(),
                user=approver,
                state=state,
                comments=comments,
            )

        # A plan approved by status is created before the setting selects the workflow, so it has none.
        golden_config_setting.config_plan_approval_workflow = None
        golden_config_setting.save()
        create_sample_plan(ConfigPlanTypeChoice.TYPE_MANUAL, "legacy", status=Status.objects.get(name="Not Approved"))

        golden_config_setting.config_plan_approval_workflow = definition
        golden_config_setting.save()
        # A device resolves to its setting through the cached membership of the setting's Dynamic Group.
        golden_config_setting.dynamic_group.update_cached_members()
        create_sample_plan(ConfigPlanTypeChoice.TYPE_INTENDED, "pending")
        denied_plan = create_sample_plan(ConfigPlanTypeChoice.TYPE_MISSING, "denied")
        respond(denied_plan, "Denied", "Missing change control URL.")
        approved_plan = create_sample_plan(ConfigPlanTypeChoice.TYPE_REMEDIATION, "approved")
        respond(approved_plan, "Approved", "Reviewed, looks good.")

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
            ConfigPlan.objects.using(options["database"]).filter(
                change_control_id__startswith=APPROVAL_SAMPLE_PREFIX
            ).delete()
            ApprovalWorkflowDefinition.objects.using(options["database"]).filter(name=APPROVAL_DEFINITION_NAME).delete()
            Group.objects.using(options["database"]).filter(name=APPROVERS_GROUP_NAME).delete()
            get_user_model().objects.using(options["database"]).filter(username=APPROVER_USERNAME).delete()

        self._generate_static_data(db=options["database"])

        self.stdout.write(self.style.SUCCESS(f"Database {options['database']} populated with app data successfully!"))
