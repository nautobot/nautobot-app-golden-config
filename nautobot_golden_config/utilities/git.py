"""Git helper methods and class."""

import logging

from git.exc import GitCommandError
from nautobot.apps.utils import GitRepo as _GitRepo

LOGGER = logging.getLogger(__name__)

_NON_FAST_FORWARD_MARKERS = (
    "non-fast-forward",
    "failed to push some refs",
    "fetch first",
    "[rejected]",
)


def _is_non_fast_forward(exc: GitCommandError) -> bool:
    """Return True when a push failure looks like a non-fast-forward rejection."""
    stderr = getattr(exc, "stderr", None) or ""
    if isinstance(stderr, bytes):
        stderr = stderr.decode("utf-8", errors="replace")
    stderr = stderr.lower()
    return any(marker in stderr for marker in _NON_FAST_FORWARD_MARKERS)


class GitRepo(_GitRepo):  # pylint: disable=too-many-instance-attributes
    """Git Repo object to help with git actions."""

    def __init__(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        path,
        url,
        clone_initially=True,
        base_url=None,
        nautobot_repo_obj=None,
    ):
        """Set attributes to easily interact with Git Repositories."""
        super().__init__(path, url, clone_initially)
        self.base_url = base_url
        self.nautobot_repo_obj = nautobot_repo_obj

    def commit_with_added(self, commit_description):
        """Make a force commit.

        Args:
            commit_description (str): the description of commit
        """
        LOGGER.debug("Committing with message `%s`", commit_description)
        self.repo.git.add(self.repo.untracked_files)
        self.repo.git.add(update=True)
        self.repo.index.commit(commit_description)
        LOGGER.debug("Commit completed")

    def push(self, max_retries: int = 3) -> None:
        """Push latest to the git repo, recovering from concurrent-update rejections.

        When a push is rejected as non-fast-forward (another worker pushed first),
        fetch from origin, rebase the local branch onto the remote tip, and retry
        the push up to ``max_retries`` times. Other ``GitCommandError`` failures
        (auth, network, etc.) are re-raised immediately. If a rebase produces a
        true conflict, the rebase is aborted and the error is surfaced.

        Args:
            max_retries (int): Maximum push attempts before giving up.
        """
        for attempt in range(1, max_retries + 1):
            try:
                LOGGER.debug("Push changes to repo (attempt %d/%d)", attempt, max_retries)
                self.repo.remotes.origin.push().raise_if_error()
                return
            except GitCommandError as exc:
                if not _is_non_fast_forward(exc) or attempt == max_retries:
                    raise
                LOGGER.debug(
                    "Push attempt %d/%d rejected as non-fast-forward; fetching and rebasing onto remote.",
                    attempt,
                    max_retries,
                )
                self.fetch()
                branch = self.repo.active_branch.name
                try:
                    self.repo.git.rebase(f"origin/{branch}")
                except GitCommandError:
                    LOGGER.debug("Rebase onto origin/%s failed; aborting and surfacing error.", branch)
                    self.repo.git.rebase("--abort")
                    raise
