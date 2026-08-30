"""Unit tests for config_deployment.py."""

from unittest.mock import MagicMock, Mock, patch

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from nautobot.apps.testing import TestCase
from nautobot.dcim.models import Device
from nautobot.extras.choices import ApprovalWorkflowStateChoices
from nautobot.extras.models import JobResult, Status
from nautobot.extras.models.approvals import ApprovalWorkflow, ApprovalWorkflowDefinition
from nornir_nautobot.exceptions import NornirNautobotException

from nautobot_golden_config.exceptions import ConfigPlanDeploymentFailure
from nautobot_golden_config.models import ConfigPlan
from nautobot_golden_config.nornir_plays.config_deployment import config_deployment
from nautobot_golden_config.tests.conftest import create_device


def _attach_workflow(plan, state):
    """Attach an ApprovalWorkflow in the given state to ``plan``."""
    workflow_def = ApprovalWorkflowDefinition.objects.filter(name="Config Plan Approval").first()
    ApprovalWorkflow.objects.create(
        approval_workflow_definition=workflow_def,
        object_under_review_content_type=ContentType.objects.get_for_model(ConfigPlan),
        object_under_review_object_id=plan.pk,
        current_state=state,
    )


class ConfigDeploymentTest(TestCase):
    """Unit tests for config_deployment.py."""

    @classmethod
    def setUpTestData(cls):
        """Set up test fixtures."""
        super().setUpTestData()
        create_device()
        cls.device = Device.objects.first()
        cls.plan_result = JobResult.objects.create(
            name="Test Plan Result",
            status=Status.objects.get(name="Completed"),
        )
        cls.config_plan = ConfigPlan.objects.create(
            plan_type="manual",
            device=cls.device,
            config_set="Test Config Set",
            plan_result=cls.plan_result,
        )
        # The save() override creates a Pending workflow because 0032 seeds a definition.
        # Flip it to Approved so the deploy gate lets us through for the happy-path tests.
        cls.config_plan.associated_approval_workflows.update(current_state=ApprovalWorkflowStateChoices.APPROVED)
        cls.user, _ = get_user_model().objects.get_or_create(username="testuser")

        # Create mock job
        cls.job = MagicMock()
        cls.job.data = {"config_plan": ConfigPlan.objects.all()}
        cls.job.celery_kwargs = {"nautobot_job_user_id": cls.user.id}
        cls.job.job_result = Mock()
        cls.job.logger.getEffectiveLevel = Mock(return_value=0)

    @patch("nautobot_golden_config.nornir_plays.config_deployment.InitNornir")
    def test_config_deployment_success(self, mock_nornir):
        """Test successful config deployment."""
        # Mock the nornir run results
        mock_host = Mock()
        mock_host.name = self.device.name
        mock_result = Mock()
        mock_result.failed = False
        mock_result.changed = True
        mock_results = Mock()
        mock_results.failed = False

        # Set up the mock nornir object and run method
        mock_nr = Mock()
        mock_nr.with_processors.return_value = mock_nr
        mock_nr.run.return_value = mock_results
        mock_nornir.return_value.__enter__.return_value = mock_nr

        # Run the deployment
        config_deployment(self.job)

        # Verify nornir was called
        mock_nornir.assert_called_once()
        mock_nr.run.assert_called_once()

    @patch("nautobot_golden_config.nornir_plays.config_deployment.InitNornir")
    def test_config_deployment_failure(self, mock_nornir):
        """Test failed config deployment raises ConfigPlanDeploymentFailure."""
        # Mock the nornir run results for failure scenario
        mock_host = Mock()
        mock_host.name = self.device.name
        mock_result = Mock()
        mock_result.failed = True
        mock_result.changed = False
        mock_results = Mock()
        mock_results.failed = True

        # Set up the mock nornir object and run method
        mock_nr = Mock()
        mock_nr.with_processors.return_value = mock_nr
        mock_nr.run.return_value = mock_results
        mock_nornir.return_value.__enter__.return_value = mock_nr

        # Run the deployment and expect ConfigPlanDeploymentFailure
        with self.assertRaises(ConfigPlanDeploymentFailure):
            config_deployment(self.job)

        # Verify nornir was called
        mock_nornir.assert_called_once()
        mock_nr.run.assert_called_once()


class ConfigDeploymentApprovalGateTest(TestCase):
    """Verify the deploy-time approval gate (E3025)."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        create_device()
        cls.device = Device.objects.first()
        cls.plan_result = JobResult.objects.create(
            name="Test Plan Result Approval",
            status=Status.objects.get(name="Completed"),
        )
        cls.user, _ = get_user_model().objects.get_or_create(username="testuser-approval")

    def _build_job(self, plan_qs):
        job = MagicMock()
        job.data = {"config_plan": plan_qs}
        job.celery_kwargs = {"nautobot_job_user_id": self.user.id}
        job.job_result = Mock()
        job.logger.getEffectiveLevel = Mock(return_value=0)
        return job

    def test_pending_workflow_blocks_deployment(self):
        plan = ConfigPlan.objects.create(
            plan_type="manual",
            device=self.device,
            config_set="Pending",
            plan_result=self.plan_result,
        )
        # The save() override created a Pending workflow; leave it Pending.
        with self.assertRaises(NornirNautobotException) as cm:
            config_deployment(self._build_job(ConfigPlan.objects.filter(pk=plan.pk)))
        self.assertIn("E3025", str(cm.exception))

    def test_denied_workflow_blocks_deployment(self):
        plan = ConfigPlan.objects.create(
            plan_type="manual",
            device=self.device,
            config_set="Denied",
            plan_result=self.plan_result,
        )
        plan.associated_approval_workflows.update(current_state=ApprovalWorkflowStateChoices.DENIED)
        with self.assertRaises(NornirNautobotException) as cm:
            config_deployment(self._build_job(ConfigPlan.objects.filter(pk=plan.pk)))
        self.assertIn("E3025", str(cm.exception))

    @patch("nautobot_golden_config.nornir_plays.config_deployment.InitNornir")
    def test_no_workflow_definition_allows_deployment(self, mock_nornir):
        # Simulate admin disabling approvals by removing the workflow definition.
        # Plans created while disabled have no associated workflows.
        ApprovalWorkflowDefinition.objects.filter(name="Config Plan Approval").delete()

        plan = ConfigPlan.objects.create(
            plan_type="manual",
            device=self.device,
            config_set="No workflow",
            plan_result=self.plan_result,
        )
        self.assertFalse(plan.associated_approval_workflows.exists())

        mock_nr = Mock()
        mock_nr.with_processors.return_value = mock_nr
        mock_results = Mock()
        mock_results.failed = False
        mock_nr.run.return_value = mock_results
        mock_nornir.return_value.__enter__.return_value = mock_nr

        config_deployment(self._build_job(ConfigPlan.objects.filter(pk=plan.pk)))
        mock_nr.run.assert_called_once()
