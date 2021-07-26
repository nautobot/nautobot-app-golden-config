"""Unit tests for nautobot_golden_config utilities git."""

import unittest
from unittest.mock import patch, Mock
from nautobot_golden_config.utilities.git import GitRepo


class GitRepoTest(unittest.TestCase):
    """Test Git Utility."""

    def setUp(self):
        """Setup a reusable mock object to pass into GitRepo."""
        mock_obj = Mock()
        mock_obj.filesystem_path = "/fake/path"
        mock_obj.remote_url = "/fake/remote"
        mock_obj._token = "fake token"  # pylint: disable=protected-access
        self.mock_obj = mock_obj

    @patch("nautobot_golden_config.utilities.git.Repo", autospec=True)
    def test_gitrepo_path_noexist(self, mock_repo):
        """Test Repo is not called when path isn't valid, ensure clone is called."""
        self.mock_obj.username = None
        GitRepo(self.mock_obj)
        mock_repo.assert_not_called()
        mock_repo.clone_from.assert_called_with("/fake/remote", to_path="/fake/path")

    @patch("nautobot_golden_config.utilities.git.os")
    @patch("nautobot_golden_config.utilities.git.Repo", autospec=True)
    def test_gitrepo_path_exist(self, mock_repo, mock_os):
        """Test Repo is not called when path is valid, ensure Repo is called."""
        mock_os.path.isdir.return_value = True
        self.mock_obj.username = None
        GitRepo(self.mock_obj)
        mock_repo.assert_called_once()
        mock_repo.assert_called_with(path="/fake/path")

    @patch("nautobot_golden_config.utilities.git.os")
    @patch("nautobot_golden_config.utilities.git.Repo", autospec=True)
    def test_path_exist_token_and_username(self, mock_repo, mock_os):
        """Test Repo is not called when path is valid, ensure Repo is called."""
        mock_os.path.isdir.return_value = True
        self.mock_obj.username = "Test User"
        GitRepo(self.mock_obj)
        mock_repo.assert_called_once()
        mock_repo.assert_called_with(path="/fake/path")
