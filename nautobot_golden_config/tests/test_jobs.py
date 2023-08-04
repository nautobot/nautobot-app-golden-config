"""Unit tests for nautobot_golden_config Jobs."""

from unittest.mock import MagicMock, patch, call
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
    @patch("nautobot_golden_config.jobs.refresh_git_config_contexts")
    @patch("nautobot_golden_config.jobs.refresh_git_config_context_schemas")
    def test_update_config_context_repos_success(
        self, mock_refresh_schemas, mock_refresh_contexts, mock_ensure_git_repo, mock_filter
    ):  # pylint: disable=no-self-use
        mock_job_obj = MagicMock()
        mock_job_obj.job_result = MagicMock()
        mock_job_obj.log_debug = MagicMock()
        mock_context_repo = MagicMock()
        mock_context_repo.name = "Test Config Contexts"
        mock_context_repo.provided_contents = ["extras.configcontext"]
        mock_schema_repo = MagicMock()
        mock_schema_repo.name = "Test Config Context Schemas"
        mock_schema_repo.provided_contents = ["extras.configcontextschema"]
        mock_filter.return_value = [mock_context_repo, mock_schema_repo]

        update_config_context_repos(mock_job_obj)

        mock_filter.assert_has_calls(
            [
                call(provided_contents__icontains="extras.configcontext"),
                call(provided_contents__icontains="extras.configcontextschema"),
            ]
        )
        mock_ensure_git_repo.assert_called()
        mock_ensure_git_repo.assert_has_calls(
            [
                call(repository_record=mock_context_repo, job_result=mock_job_obj.job_result),
                call(repository_record=mock_schema_repo, job_result=mock_job_obj.job_result),
            ]
        )
        mock_refresh_contexts.assert_called()
        mock_refresh_contexts.assert_has_calls(
            [
                call(repository_record=mock_context_repo, job_result=mock_job_obj.job_result),
                call(repository_record=mock_schema_repo, job_result=mock_job_obj.job_result),
            ]
        )
        mock_refresh_schemas.assert_called()
        mock_refresh_schemas.assert_called_with(repository_record=mock_schema_repo, job_result=mock_job_obj.job_result)
        mock_job_obj.log_debug.assert_has_calls(
            [
                call("Pulling config context repo Test Config Contexts."),
                call("Pulling config context repo Test Config Context Schemas."),
            ]
        )
        mock_job_obj.job_result.assert_not_called()
