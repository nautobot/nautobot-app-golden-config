"""Unit tests for the nautobot_golden_config management commands."""

from io import StringIO

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from nautobot.apps.testing import TestCase
from nautobot.dcim.models import Platform
from nautobot.extras.models.approvals import ApprovalWorkflowDefinition

from nautobot_golden_config.models import ConfigPlan, GoldenConfigSetting

from .conftest import create_device_data

SAMPLE_PLAN_PREFIX = "approval-sample-"


class GenerateTestDataCommandTestCase(TestCase):
    """Test the approval workflow data created by generate_nautobot_golden_config_test_data."""

    @classmethod
    def setUpTestData(cls):
        create_device_data()
        # Without a driver the command picks a random one, and not every parser accepts its sample configs.
        Platform.objects.update(network_driver="cisco_ios")

    def _generate(self, **options):
        call_command("generate_nautobot_golden_config_test_data", stdout=StringIO(), **options)

    def _sample_plans(self):
        return {
            plan.change_control_id.removeprefix(SAMPLE_PLAN_PREFIX): plan
            for plan in ConfigPlan.objects.filter(change_control_id__startswith=SAMPLE_PLAN_PREFIX)
        }

    def test_creates_a_sample_plan_in_each_approval_state(self):
        self._generate()

        sample_plans = self._sample_plans()
        approval_state_and_status = {
            label: (plan.approval_workflow.current_state if plan.approval_workflow else None, plan.status.name)
            for label, plan in sample_plans.items()
        }
        self.assertEqual(
            approval_state_and_status,
            {
                "legacy": (None, "Not Approved"),
                "pending": ("Pending", "Pending Approval"),
                "denied": ("Denied", "Not Approved"),
                "approved": ("Approved", "Approved"),
            },
        )

    def test_setting_selects_the_approval_workflow(self):
        self._generate()

        definition = ApprovalWorkflowDefinition.objects.get(name="Golden Config Test Config Plan Approval")
        self.assertEqual(GoldenConfigSetting.objects.get().config_plan_approval_workflow, definition)
        approvers = Group.objects.get(name="Golden Config Test Approvers")
        self.assertTrue(approvers.user_set.filter(username="gc-test-approver").exists())

    def test_flush_removes_the_approval_data(self):
        self._generate()
        self._generate(flush=True)

        self.assertEqual(ApprovalWorkflowDefinition.objects.filter(name__startswith="Golden Config Test").count(), 1)
        self.assertEqual(len(self._sample_plans()), 4)
        self.assertEqual(Group.objects.filter(name="Golden Config Test Approvers").count(), 1)
        self.assertEqual(get_user_model().objects.filter(username="gc-test-approver").count(), 1)
