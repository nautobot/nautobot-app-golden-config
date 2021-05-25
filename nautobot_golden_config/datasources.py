"""Data source plugin extension to register additional git repo types."""
from nautobot.extras.choices import LogLevelChoices
from nautobot.extras.registry import DatasourceContent

from nautobot_golden_config.utilities.constant import ENABLE_BACKUP, ENABLE_COMPLIANCE, ENABLE_INTENDED


def refresh_git_jinja(repository_record, job_result, delete=False):  # pylint: disable=unused-argument
    """Callback for gitrepository updates on Jinja Template repo."""
    job_result.log(
        "Successfully Pulled git repo",
        level_choice=LogLevelChoices.LOG_SUCCESS,
    )


def refresh_git_intended(repository_record, job_result, delete=False):  # pylint: disable=unused-argument
    """Callback for gitrepository updates on Intended Config repo."""
    job_result.log(
        "Successfully Pulled git repo",
        level_choice=LogLevelChoices.LOG_SUCCESS,
    )


def refresh_git_backup(repository_record, job_result, delete=False):  # pylint: disable=unused-argument
    """Callback for gitrepository updates on Git Backup repo."""
    job_result.log(
        "Successfully Pulled git repo",
        level_choice=LogLevelChoices.LOG_SUCCESS,
    )


datasource_contents = []
if ENABLE_INTENDED or ENABLE_COMPLIANCE:
    datasource_contents.append(
        (
            "extras.gitrepository",
            DatasourceContent(
                name="intended configs",
                content_identifier="nautobot_golden_config.intendedconfigs",
                icon="mdi-file-document-outline",
                callback=refresh_git_intended,
            ),
        )
    )
if ENABLE_INTENDED:
    datasource_contents.append(
        (
            "extras.gitrepository",
            DatasourceContent(
                name="jinja templates",
                content_identifier="nautobot_golden_config.jinjatemplate",
                icon="mdi-text-box-check-outline",
                callback=refresh_git_jinja,
            ),
        )
    )
if ENABLE_BACKUP or ENABLE_COMPLIANCE:
    datasource_contents.append(
        (
            "extras.gitrepository",
            DatasourceContent(
                name="backup configs",
                content_identifier="nautobot_golden_config.backupconfigs",
                icon="mdi-file-code",
                callback=refresh_git_backup,
            ),
        )
    )
