"""Git helper methods and class."""

import logging

from nautobot.core.utils.git import GitRepo as _GitRepo

LOGGER = logging.getLogger(__name__)


class GitRepo(_GitRepo):  # pylint: disable=too-many-instance-attributes
    """Git Repo object to help with git actions."""

    def __init__(  # pylint: disable=too-many-arguments
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

    def push(self):
        """Push latest to the git repo."""
        LOGGER.debug("Push changes to repo")
        self.repo.remotes.origin.push().raise_if_error()
