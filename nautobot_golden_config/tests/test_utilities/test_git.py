"""Unit tests for nautobot_golden_config utilities git."""

import unittest
from unittest.mock import ANY, Mock, patch
from urllib.parse import quote

from django.conf import settings
from git.exc import GitCommandError
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


@patch("nautobot.core.utils.git.os.path.isdir", Mock(return_value=True))
@patch("nautobot.core.utils.git.Repo", autospec=True)
class GitRepoPushTest(unittest.TestCase):
    """Test GitRepo.push() concurrent-push handling (issue #968)."""

    PATH = "/fake/path"
    URL = "https://fake.git/org/repository.git"

    @staticmethod
    def _non_fast_forward_error():
        return GitCommandError(
            "git push",
            1,
            stderr=b"! [rejected]        main -> main (non-fast-forward)\nerror: failed to push some refs to 'origin'\n",
        )

    def test_push_retries_on_non_fast_forward_then_succeeds(self, _mock_repo_cls):
        """Regression test for #968.

        When the remote rejects the initial push as non-fast-forward, push() must fetch from origin,
        rebase the local branch onto the remote tip, and retry the push so that two concurrent jobs
        can both succeed.
        """
        git_repo = GitRepo(self.PATH, self.URL, base_url=self.URL)
        repo = git_repo.repo
        repo.active_branch.name = "main"

        push_result = Mock()
        push_result.raise_if_error.side_effect = [self._non_fast_forward_error(), None]
        repo.remotes.origin.push.return_value = push_result

        with patch.object(GitRepo, "fetch") as mock_fetch:
            git_repo.push()

        self.assertEqual(repo.remotes.origin.push.call_count, 2)
        self.assertEqual(push_result.raise_if_error.call_count, 2)
        mock_fetch.assert_called_once_with()
        repo.git.rebase.assert_called_once_with("origin/main")

    def test_push_succeeds_first_try_no_fetch_or_rebase(self, _mock_repo_cls):
        """Happy path: a successful push must not fetch or rebase."""
        git_repo = GitRepo(self.PATH, self.URL, base_url=self.URL)
        repo = git_repo.repo

        push_result = Mock()
        push_result.raise_if_error.return_value = None
        repo.remotes.origin.push.return_value = push_result

        with patch.object(GitRepo, "fetch") as mock_fetch:
            git_repo.push()

        repo.remotes.origin.push.assert_called_once_with()
        push_result.raise_if_error.assert_called_once_with()
        mock_fetch.assert_not_called()
        repo.git.rebase.assert_not_called()

    def test_push_rebase_conflict_aborts_and_reraises(self, _mock_repo_cls):
        """A rebase that itself fails must abort and surface the original error, not loop."""
        git_repo = GitRepo(self.PATH, self.URL, base_url=self.URL)
        repo = git_repo.repo
        repo.active_branch.name = "main"

        push_result = Mock()
        push_result.raise_if_error.side_effect = self._non_fast_forward_error()
        repo.remotes.origin.push.return_value = push_result

        rebase_conflict = GitCommandError("git rebase", 1, stderr=b"CONFLICT (content): Merge conflict in foo.cfg")
        repo.git.rebase.side_effect = [rebase_conflict, None]

        with patch.object(GitRepo, "fetch"), self.assertRaises(GitCommandError):
            git_repo.push()

        self.assertEqual(repo.remotes.origin.push.call_count, 1)
        self.assertEqual(repo.git.rebase.call_count, 2)
        repo.git.rebase.assert_any_call("origin/main")
        repo.git.rebase.assert_any_call("--abort")

    def test_push_non_retryable_error_fails_fast(self, _mock_repo_cls):
        """Auth/network errors must propagate immediately without fetch or rebase."""
        git_repo = GitRepo(self.PATH, self.URL, base_url=self.URL)
        repo = git_repo.repo

        auth_error = GitCommandError("git push", 128, stderr=b"fatal: Authentication failed for 'origin'")
        push_result = Mock()
        push_result.raise_if_error.side_effect = auth_error
        repo.remotes.origin.push.return_value = push_result

        with patch.object(GitRepo, "fetch") as mock_fetch, self.assertRaises(GitCommandError):
            git_repo.push()

        self.assertEqual(repo.remotes.origin.push.call_count, 1)
        mock_fetch.assert_not_called()
        repo.git.rebase.assert_not_called()

    def test_push_exhausts_retries(self, _mock_repo_cls):
        """If every attempt is rejected as non-fast-forward, the error propagates after max_retries."""
        git_repo = GitRepo(self.PATH, self.URL, base_url=self.URL)
        repo = git_repo.repo
        repo.active_branch.name = "main"

        push_result = Mock()
        push_result.raise_if_error.side_effect = [
            self._non_fast_forward_error(),
            self._non_fast_forward_error(),
            self._non_fast_forward_error(),
        ]
        repo.remotes.origin.push.return_value = push_result

        with patch.object(GitRepo, "fetch") as mock_fetch, self.assertRaises(GitCommandError):
            git_repo.push(max_retries=3)

        self.assertEqual(repo.remotes.origin.push.call_count, 3)
        self.assertEqual(mock_fetch.call_count, 2)
        self.assertEqual(repo.git.rebase.call_count, 2)
