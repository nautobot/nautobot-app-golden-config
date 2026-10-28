"""Unit tests for config_deployment.py."""

from unittest.mock import MagicMock, Mock, patch

from django.contrib.auth import get_user_model
from nautobot.apps.choices import ApprovalWorkflowStateChoices
from nautobot.apps.testing import TestCase
from nautobot.dcim.models import Device
from nautobot.extras.models import JobResult, Status

from nautobot_golden_config.exceptions import ConfigPlanDeploymentFailure, ConfigPlanNotApproved
from nautobot_golden_config.models import ConfigPlan
from nautobot_golden_config.nornir_plays.config_deployment import config_deployment
from nautobot_golden_config.tests.conftest import create_device, enable_config_plan_approval


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
            status=Status.objects.get(name="Approved"),
            plan_result=cls.plan_result,
        )
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
    """Test that only approved config plans are deployed."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.device = create_device()
        cls.setting, _, _ = enable_config_plan_approval()
        cls.plan_result = JobResult.objects.create(name="Test Plan Result", status=Status.objects.get(name="Completed"))
        cls.user, _ = get_user_model().objects.get_or_create(username="testuser")

    def _create_plan(self, plan_type="manual", status_name="Not Approved"):
        return ConfigPlan.objects.create(
            plan_type=plan_type,
            device=self.device,
            config_set="hostname test",
            plan_result=self.plan_result,
            status=Status.objects.get(name=status_name),
        )

    def _set_workflow_state(self, plan, state):
        plan.associated_approval_workflows.update(current_state=state)

    def _disable_approval_workflow(self):
        self.setting.config_plan_approval_workflow = None
        self.setting.validated_save()

    def _build_job(self, *plans):
        job = MagicMock()
        job.data = {"config_plan": ConfigPlan.objects.filter(pk__in=[plan.pk for plan in plans])}
        job.celery_kwargs = {"nautobot_job_user_id": self.user.id}
        job.job_result = Mock()
        job.logger.getEffectiveLevel = Mock(return_value=0)
        return job

    def _mock_successful_nornir(self, mock_nornir):
        mock_nr = Mock()
        mock_nr.with_processors.return_value = mock_nr
        mock_nr.run.return_value = Mock(failed=False)
        mock_nornir.return_value.__enter__.return_value = mock_nr
        return mock_nr

    @patch("nautobot_golden_config.nornir_plays.config_deployment.InitNornir")
    def test_plan_with_approved_workflow_is_deployed(self, mock_nornir):
        mock_nr = self._mock_successful_nornir(mock_nornir)
        plan = self._create_plan()
        self._set_workflow_state(plan, ApprovalWorkflowStateChoices.APPROVED)
        config_deployment(self._build_job(plan))
        mock_nr.run.assert_called_once()

    @patch("nautobot_golden_config.nornir_plays.config_deployment.InitNornir")
    def test_plan_with_unapproved_workflow_is_not_deployed(self, mock_nornir):
        plan = self._create_plan()
        for state in (
            ApprovalWorkflowStateChoices.PENDING,
            ApprovalWorkflowStateChoices.DENIED,
            ApprovalWorkflowStateChoices.CANCELED,
        ):
            with self.subTest(state=state):
                self._set_workflow_state(plan, state)
                with self.assertRaisesMessage(ConfigPlanNotApproved, "E3025"):
                    config_deployment(self._build_job(plan))
        mock_nornir.assert_not_called()

    @patch("nautobot_golden_config.nornir_plays.config_deployment.InitNornir")
    def test_workflow_state_wins_over_an_approved_status(self, mock_nornir):
        plan = self._create_plan(status_name="Approved")
        with self.assertRaises(ConfigPlanNotApproved):
            config_deployment(self._build_job(plan))
        mock_nornir.assert_not_called()

    @patch("nautobot_golden_config.nornir_plays.config_deployment.InitNornir")
    def test_one_unapproved_plan_stops_the_whole_batch(self, mock_nornir):
        approved_plan = self._create_plan(plan_type="manual")
        pending_plan = self._create_plan(plan_type="missing")
        self._set_workflow_state(approved_plan, ApprovalWorkflowStateChoices.APPROVED)
        with self.assertRaisesMessage(ConfigPlanNotApproved, "Pending"):
            config_deployment(self._build_job(approved_plan, pending_plan))
        mock_nornir.assert_not_called()

    @patch("nautobot_golden_config.nornir_plays.config_deployment.InitNornir")
    def test_plan_without_workflow_is_gated_by_status(self, mock_nornir):
        self._disable_approval_workflow()
        mock_nr = self._mock_successful_nornir(mock_nornir)
        for status_name in ("Not Approved", "Pending Approval"):
            with self.subTest(status=status_name):
                plan = self._create_plan(status_name=status_name)
                self.assertIsNone(plan.approval_workflow)
                with self.assertRaisesMessage(ConfigPlanNotApproved, "E3025"):
                    config_deployment(self._build_job(plan))
                plan.delete()
        mock_nr.run.assert_not_called()

        approved_plan = self._create_plan(status_name="Approved")
        config_deployment(self._build_job(approved_plan))
        mock_nr.run.assert_called_once()
