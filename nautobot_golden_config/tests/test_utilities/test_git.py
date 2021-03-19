"""Unit tests for nautobot_golden_config utilities git.

(c) 2020-2021 Network To Code
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at
  http://www.apache.org/licenses/LICENSE-2.0
Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
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
        mock_obj._token = "fake token"
        self.mock_obj = mock_obj

    @patch("nautobot_golden_config.utilities.git.Repo", autospec=True)
    def test_gitrepo_path_noexist(self, mock_repo):
        """Test Repo is not called when path isn't valid, ensure clone is called."""
        GitRepo(self.mock_obj)
        mock_repo.assert_not_called()
        mock_repo.clone_from.assert_called_with("/fake/remote", to_path="/fake/path")

    @patch("nautobot_golden_config.utilities.git.os")
    @patch("nautobot_golden_config.utilities.git.Repo", autospec=True)
    def test_gitrepo_path_exist(self, mock_repo, mock_os):
        """Test Repo is not called when path is valid, ensure Repo is called."""
        mock_os.path.isdir.return_value = True
        GitRepo(self.mock_obj)
        mock_repo.assert_called_once()
        mock_repo.assert_called_with(path="/fake/path")
