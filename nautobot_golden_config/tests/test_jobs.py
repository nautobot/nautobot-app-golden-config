"""Unit tests for nautobot_golden_config Jobs."""

from unittest.mock import MagicMock, patch
from nautobot.utilities.testing import TransactionTestCase

from nautobot_golden_config.jobs import update_config_context_repos


class JobHelperTests(TransactionTestCase):
    """Unit tests for the helper methods for Jobs."""

    databases = (
        "default",
        "job_logs",
    )

    @patch("nautobot.extras.models.GitRepository.objects.filter")
    @patch("nautobot_golden_config.jobs.ensure_git_repository")
    def test_update_config_context_repos_success(self, mock_ensure_git_repo, mock_filter):
        mock_job_obj = MagicMock()
        mock_job_obj.job_result = MagicMock()
        mock_job_obj.log_debug = MagicMock()
        mock_git_repo = MagicMock()
        mock_git_repo.name = "Test"
        mock_git_repo.provided_contents = ["extras.configcontext"]
        mock_filter.return_value = [mock_git_repo]

        update_config_context_repos(mock_job_obj)

        mock_filter.assert_called_once_with(provided_contents__icontains="extras.configcontext")
        mock_ensure_git_repo.assert_called_once()
        mock_ensure_git_repo.assert_called_with(repository_record=mock_git_repo, job_result=mock_job_obj.job_result)
        mock_job_obj.log_debug.assert_called_once_with("Pulling config context repo Test.")
        mock_job_obj.job_result.assert_not_called()
