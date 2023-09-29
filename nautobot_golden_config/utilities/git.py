"""Git helper methods and class."""

import logging
import os
import re
from urllib.parse import quote

from git import Repo
from nautobot.core.utils.git import GIT_ENVIRONMENT
from nautobot.core.utils.git import GitRepo as _GitRepo

from nautobot.extras.choices import SecretsGroupSecretTypeChoices
from nautobot.extras.datasources.git import get_repo_from_url_to_path_and_from_branch
from nautobot_golden_config.utilities.utils import get_secret_value


LOGGER = logging.getLogger(__name__)


class GitRepo(_GitRepo):  # pylint: disable=too-many-instance-attributes
    """Git Repo object to help with git actions."""

    def __init__(self, path, url, clone_initially=True, *args, **kwargs):
        """Set attributes to easily interact with Git Repositories."""
        super().__init__(path, url, clone_initially)
        self.remote_url = kwargs["remote_url"]

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
