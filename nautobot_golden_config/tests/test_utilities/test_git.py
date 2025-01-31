"""Unit tests for nautobot_golden_config utilities git."""

import unittest
from unittest.mock import ANY, Mock, patch
from urllib.parse import quote

from django.conf import settings
from nautobot.extras.datasources.git import get_repo_from_url_to_path_and_from_branch
from packaging import version

from nautobot_golden_config.utilities.git import GitRepo


class GitRepoTest(unittest.TestCase):
    """Test Git Utility."""

    def setUp(self):
        """Setup a reusable mock object to pass into GitRepo."""
        mock_obj = Mock()

        def mock_get_secret_value(  # pylint: disable=unused-argument,inconsistent-return-statements
            access_type, secret_type, **kwargs
        ):
            """Mock SecretsGroup.get_secret_value()."""
            if secret_type == "username":
                return mock_obj.username
            if secret_type == "token":
                return mock_obj._token  # pylint: disable=protected-access

        mock_obj.filesystem_path = "/fake/path"
        mock_obj.remote_url = "https://fake.git/org/repository.git"
        mock_obj._token = "fake token"  # pylint: disable=protected-access
        mock_obj.username = None
        mock_obj.secrets_group = Mock(get_secret_value=mock_get_secret_value)
        self.mock_obj = mock_obj

        # Different behavior of `Repo.clone_from` in different versions of Nautobot. `branch` kwarg added in 2.4.2
        self.clone_from_kwargs = {"to_path": self.mock_obj.filesystem_path, "env": None}
        if version.parse(settings.VERSION) >= version.parse("2.4.2"):
            self.clone_from_kwargs["branch"] = ANY

    @patch("nautobot.core.utils.git.GIT_ENVIRONMENT", None)
    @patch("nautobot.core.utils.git.os.path.isdir", Mock(return_value=False))
    @patch("nautobot.core.utils.git.Repo", autospec=True)
    def test_gitrepo_path_noexist(self, mock_repo):
        """Test Repo is not called when path isn't valid, ensure clone_from is called."""
        git_info = get_repo_from_url_to_path_and_from_branch(self.mock_obj)
        GitRepo(self.mock_obj.filesystem_path, git_info.from_url, base_url=self.mock_obj.remote_url)
        mock_repo.assert_not_called()
        mock_repo.clone_from.assert_called_with(git_info.from_url, **self.clone_from_kwargs)

    @patch("nautobot.core.utils.git.os.path.isdir", Mock(return_value=True))
    @patch("nautobot.core.utils.git.Repo", autospec=True)
    def test_gitrepo_path_exist(self, mock_repo):
        """Test Repo is called when path is valid."""
        git_info = get_repo_from_url_to_path_and_from_branch(self.mock_obj)
        GitRepo(self.mock_obj.filesystem_path, git_info.from_url, base_url=self.mock_obj.remote_url)
        mock_repo.assert_called_once_with(path=self.mock_obj.filesystem_path)

    @patch("nautobot.core.utils.git.GIT_ENVIRONMENT", None)
    @patch("nautobot.core.utils.git.os.path.isdir", Mock(return_value=False))
    @patch("nautobot.core.utils.git.Repo", autospec=True)
    def test_path_noexist_token_and_username_with_symbols(self, mock_repo):
        """Test Repo clone_from is called when path is not valid, with username and token."""
        self.mock_obj.username = "Test User"
        self.mock_obj._token = "Fake Token"  # pylint: disable=protected-access
        git_info = get_repo_from_url_to_path_and_from_branch(self.mock_obj)
        self.assertIn(quote(self.mock_obj.username), git_info.from_url)
        self.assertIn(quote(self.mock_obj._token), git_info.from_url)  # pylint: disable=protected-access
        GitRepo(self.mock_obj.filesystem_path, git_info.from_url, base_url=self.mock_obj.remote_url)
        mock_repo.assert_not_called()
        mock_repo.clone_from.assert_called_with(git_info.from_url, **self.clone_from_kwargs)
