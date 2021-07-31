"""Git helper methods and class."""

import os
import re
import logging

from urllib.parse import quote

from git import Repo


LOGGER = logging.getLogger(__name__)


class GitRepo:
    """Git Repo object to help with git actions."""

    def __init__(self, obj):
        """Set attributes to easily interact with Git Repositories.

        Args:
            obj (GitRepository): Django ORM object from GitRepository.
        """
        self.path = obj.filesystem_path
        self.url = obj.remote_url
        self.token = obj._token
        self.token_user = obj.username
        if self.token and self.token not in self.url:
            # Some Git Providers require a user as well as a token.
            if self.token_user:
                self.url = re.sub("//", f"//{quote(self.token_user, safe='')}:{quote(self.token, safe='')}@", self.url)
            else:
                # Github only requires the token.
                self.url = re.sub("//", f"//{quote(self.token, safe='')}@", self.url)

        self.branch = obj.branch
        self.obj = obj

        if os.path.isdir(self.path):
            LOGGER.debug("Git path `%s` exists, initiate", self.path)
            self.repo = Repo(path=self.path)
        else:
            LOGGER.debug("Git path `%s` does not exists, clone", self.path)
            self.repo = Repo.clone_from(self.url, to_path=self.path)

        if self.url not in self.repo.remotes.origin.urls:
            LOGGER.debug("URL `%s` was not currently set, setting", self.url)
            self.repo.remotes.origin.set_url(self.url)

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
        self.repo.remotes.origin.push()
