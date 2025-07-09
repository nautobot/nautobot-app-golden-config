"""Unit tests for config_deployment.py."""

import unittest
from unittest.mock import MagicMock, Mock, patch

from django.contrib.auth import get_user_model
from nautobot.dcim.models import Device
from nautobot.extras.models import JobResult, Status

from nautobot_golden_config.exceptions import ConfigPlanDeploymentFailure
from nautobot_golden_config.models import ConfigPlan
from nautobot_golden_config.nornir_plays.config_deployment import config_deployment


class ConfigDeploymentTest(unittest.TestCase):
    """Unit tests for config_deployment.py."""

    def setUp(self):
        """Set up test fixtures."""
        self.device = Device.objects.first()
        self.plan_result = JobResult.objects.create(
            name="Test Plan Result",
            status=Status.objects.get(name="Completed"),
        )
        self.config_plan = ConfigPlan.objects.create(
            plan_type="manual",
            device=self.device,
            config_set="Test Config Set",
            status=Status.objects.get(name="Approved"),
            plan_result=self.plan_result,
        )

        # Create mock job
        self.job = MagicMock()
        self.job.data = {"config_plan": ConfigPlan.objects.all()}
        self.job.celery_kwargs = {"nautobot_job_user_id": get_user_model().objects.first().id}
        self.job.job_result = Mock()
        self.job.logger.getEffectiveLevel = Mock(return_value=0)

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
