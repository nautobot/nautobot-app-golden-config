"""Unit tests for config_deployment.py."""

from unittest.mock import MagicMock, Mock, patch

from django.contrib.auth import get_user_model
from nautobot.apps.testing import TestCase
from nautobot.dcim.models import Device
from nautobot.extras.models import JobResult, Status

from nautobot_golden_config.exceptions import ConfigPlanDeploymentFailure
from nautobot_golden_config.models import ConfigPlan
from nautobot_golden_config.nornir_plays.config_deployment import config_deployment
from nautobot_golden_config.tests.conftest import create_device


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
