"""Basic Job Test."""

from unittest.mock import MagicMock, patch

from nautobot.apps.testing import TransactionTestCase, create_job_result_and_run_job
from nautobot.dcim.models import Device
from nautobot.extras.models import JobLogEntry

from nautobot_golden_config import jobs
from nautobot_golden_config.models import GoldenConfigSetting
from nautobot_golden_config.tests.conftest import (
    create_device,
    create_orphan_device,
    dgs_gc_settings_and_job_repo_objects,
)


class BaseGoldenConfigTestCase(TransactionTestCase):
    """Base test case with helper methods for GoldenConfigSetting."""

    def setUp(self):
        super().setUp()
        self.settings = GoldenConfigSetting.objects.first()
        self.settings.backup_enabled = True
        self.settings.intended_enabled = True
        self.settings.compliance_enabled = True
        self.settings.plan_enabled = True
        self.settings.deploy_enabled = True
        self.settings.save()

    def tearDown(self):
        self.settings.backup_enabled = True
        self.settings.intended_enabled = True
        self.settings.compliance_enabled = True
        self.settings.plan_enabled = True
        self.settings.deploy_enabled = True
        self.settings.save()
        super().tearDown()

    def update_golden_config_settings(  # pylint: disable=too-many-arguments
        self,
        backup_enabled=None,
        intended_enabled=None,
        compliance_enabled=None,
        plan_enabled=None,
        deploy_enabled=None,
    ):
        """Update fields of the GoldenConfigSetting instance."""
        if backup_enabled is not None:
            self.settings.backup_enabled = backup_enabled
        if intended_enabled is not None:
            self.settings.intended_enabled = intended_enabled
        if compliance_enabled is not None:
            self.settings.compliance_enabled = compliance_enabled
        if plan_enabled is not None:
            self.settings.plan_enabled = plan_enabled
        if deploy_enabled is not None:
            self.settings.deploy_enabled = deploy_enabled
        self.settings.save()


@patch("nautobot_golden_config.nornir_plays.config_backup.run_backup", MagicMock(return_value="foo"))
@patch.object(jobs, "ensure_git_repository")
class GCReposBackupTestCase(BaseGoldenConfigTestCase):
    """Test the repos to sync and commit are working for backup job."""

    databases = ("default", "job_logs")

    def setUp(self) -> None:
        """Setup test data."""
        self.device = create_device(name="foobaz")
        self.device2 = create_orphan_device(name="foobaz2")
        dgs_gc_settings_and_job_repo_objects()
        super().setUp()

    def test_backup_job_repos_one_setting(self, mock_ensure_git_repository):
        """Test backup job repo-types are backup only."""
        mock_ensure_git_repository.return_value = True
        self.update_golden_config_settings(backup_enabled=True)
        job_result = create_job_result_and_run_job(
            module="nautobot_golden_config.jobs", name="BackupJob", device=Device.objects.filter(name=self.device.name)
        )

        log_entries = JobLogEntry.objects.filter(job_result=job_result, grouping="GC Repo Syncs")
        self.assertEqual(log_entries.first().message, "Repository types to sync: backup_repository")

        log_entries = JobLogEntry.objects.filter(job_result=job_result, grouping="Get Job Filter")
        self.assertEqual(log_entries.count(), 2)
        self.assertEqual(log_entries.last().message, "In scope device count for this job: 1")

        log_entries = JobLogEntry.objects.filter(job_result=job_result, grouping="GC After Run")
        self.assertEqual(log_entries.first().message, "Finished the Backup Configurations job execution.")

        log_entries = JobLogEntry.objects.filter(job_result=job_result, grouping="GC Repo Commit and Push")
        self.assertEqual(log_entries.count(), 1)

    def test_backup_job_repos_two_setting(self, mock_ensure_git_repository):
        """Test backup job repo-types are backup only."""
        mock_ensure_git_repository.return_value = True
        self.update_golden_config_settings(backup_enabled=True)
        job_result = create_job_result_and_run_job(
            module="nautobot_golden_config.jobs",
            name="BackupJob",
            device=Device.objects.all(),
        )

        log_entries = JobLogEntry.objects.filter(job_result=job_result, grouping="Get Job Filter")
        self.assertEqual(log_entries.count(), 2)
        self.assertEqual(log_entries.last().message, "In scope device count for this job: 2")

        log_entries = JobLogEntry.objects.filter(job_result=job_result, grouping="GC Repo Syncs")
        self.assertEqual(log_entries.first().message, "Repository types to sync: backup_repository")

        log_entries = JobLogEntry.objects.filter(job_result=job_result, grouping="GC After Run")
        self.assertEqual(log_entries.first().message, "Finished the Backup Configurations job execution.")

        log_entries = JobLogEntry.objects.filter(job_result=job_result, grouping="GC Repo Commit and Push")
        self.assertEqual(log_entries.count(), 1)

    def test_backup_job_repos_one_setting_backup_disabled(self, mock_ensure_git_repository):
        """Test backup job repo-types are backup only."""
        mock_ensure_git_repository.return_value = True
        self.update_golden_config_settings(backup_enabled=False)

        job_result = create_job_result_and_run_job(
            module="nautobot_golden_config.jobs", name="BackupJob", device=Device.objects.filter(name=self.device.name)
        )
        log_entries = JobLogEntry.objects.filter(job_result=job_result, grouping="GC Repo Syncs")
        self.assertEqual(log_entries.first().message, "Repository types to sync: ")

        log_entries = JobLogEntry.objects.filter(job_result=job_result, grouping="Get Job Filter")
        self.assertEqual(log_entries.count(), 2)
        self.assertEqual(log_entries.last().message, "In scope device count for this job: 1")

        log_entries = JobLogEntry.objects.filter(job_result=job_result, grouping="run")
        self.assertEqual(
            log_entries.last().message, "`E3032:` The backup feature is disabled in Golden Config settings."
        )

    def test_backup_job_repos_two_setting_backup_disabled(self, mock_ensure_git_repository):
        """Test backup job repo-types are backup only."""
        mock_ensure_git_repository.return_value = True
        self.update_golden_config_settings(backup_enabled=False)
        job_result = create_job_result_and_run_job(
            module="nautobot_golden_config.jobs", name="BackupJob", device=Device.objects.all()
        )
        log_entries = JobLogEntry.objects.filter(job_result=job_result, grouping="GC Repo Syncs")
        self.assertEqual(log_entries.first().message, "Repository types to sync: ")

        log_entries = JobLogEntry.objects.filter(job_result=job_result, grouping="Get Job Filter")
        self.assertEqual(log_entries.count(), 2)
        self.assertEqual(log_entries.last().message, "In scope device count for this job: 2")

        log_entries = JobLogEntry.objects.filter(job_result=job_result, grouping="run")
        self.assertEqual(
            log_entries.last().message, "`E3032:` The backup feature is disabled in Golden Config settings."
        )


@patch("nautobot_golden_config.nornir_plays.config_intended.run_template", MagicMock(return_value="foo"))
@patch.object(jobs, "ensure_git_repository")
class GCReposIntendedTestCase(BaseGoldenConfigTestCase):
    """Test the repos to sync and commit are working for intended job."""

    databases = ("default", "job_logs")

    def setUp(self) -> None:
        """Setup test data."""
        self.device = create_device(name="foobaz")
        self.device2 = create_orphan_device(name="foobaz2")
        dgs_gc_settings_and_job_repo_objects()
        super().setUp()

    def test_intended_job_repos_one_setting(self, mock_ensure_git_repository):
        """Test intended job one GC setting enabled_intended enabled"""
        mock_ensure_git_repository.return_value = True
        self.update_golden_config_settings(intended_enabled=True)
        job_result = create_job_result_and_run_job(
            module="nautobot_golden_config.jobs",
            name="IntendedJob",
            device=Device.objects.filter(name=self.device.name),
        )

        log_entries = JobLogEntry.objects.filter(job_result=job_result, grouping="GC Repo Syncs")
        self.assertEqual(log_entries.first().message, "Repository types to sync: intended_repository, jinja_repository")

        log_entries = JobLogEntry.objects.filter(job_result=job_result, grouping="Get Job Filter")
        self.assertEqual(log_entries.count(), 2)
        self.assertEqual(log_entries.last().message, "In scope device count for this job: 1")

        log_entries = JobLogEntry.objects.filter(job_result=job_result, grouping="GC After Run")
        self.assertEqual(log_entries.first().message, "Finished the Generate Intended Configurations job execution.")

        log_entries = JobLogEntry.objects.filter(job_result=job_result, grouping="GC Repo Commit and Push")
        self.assertEqual(log_entries.count(), 1)

    def test_intended_job_repos_two_setting(self, mock_ensure_git_repository):
        """Test intended job two GC setting enabled_intended enabled"""
        mock_ensure_git_repository.return_value = True
        self.update_golden_config_settings(intended_enabled=True)
        job_result = create_job_result_and_run_job(
            module="nautobot_golden_config.jobs", name="IntendedJob", device=Device.objects.all()
        )
        log_entries = JobLogEntry.objects.filter(job_result=job_result, grouping="Get Job Filter")
        self.assertEqual(log_entries.count(), 2)
        self.assertEqual(log_entries.last().message, "In scope device count for this job: 2")

        log_entries = JobLogEntry.objects.filter(job_result=job_result, grouping="GC Repo Syncs")
        self.assertEqual(log_entries.first().message, "Repository types to sync: intended_repository, jinja_repository")

        log_entries = JobLogEntry.objects.filter(job_result=job_result, grouping="GC After Run")
        self.assertEqual(log_entries.first().message, "Finished the Generate Intended Configurations job execution.")

        log_entries = JobLogEntry.objects.filter(job_result=job_result, grouping="GC Repo Commit and Push")
        self.assertEqual(log_entries.count(), 1)

    def test_intended_job_repos_one_setting_intended_disabled(self, mock_ensure_git_repository):
        """Test intended job one GC setting enabled_intended disabled"""
        mock_ensure_git_repository.return_value = True
        self.update_golden_config_settings(intended_enabled=False)
        job_result = create_job_result_and_run_job(
            module="nautobot_golden_config.jobs",
            name="IntendedJob",
            device=Device.objects.filter(name=self.device.name),
        )
        log_entries = JobLogEntry.objects.filter(job_result=job_result, grouping="GC Repo Syncs")
        self.assertEqual(log_entries.first().message, "Repository types to sync: ")

        log_entries = JobLogEntry.objects.filter(job_result=job_result, grouping="Get Job Filter")
        self.assertEqual(log_entries.count(), 2)
        self.assertEqual(log_entries.last().message, "In scope device count for this job: 1")

        log_entries = JobLogEntry.objects.filter(job_result=job_result, grouping="run")
        self.assertEqual(
            log_entries.last().message, "`E3032:` The intended feature is disabled in Golden Config settings."
        )

    def test_intended_job_repos_two_setting_intended_disabled(self, mock_ensure_git_repository):
        """Test intended job two GC setting enabled_intended disabled"""
        mock_ensure_git_repository.return_value = True
        self.update_golden_config_settings(intended_enabled=False)
        job_result = create_job_result_and_run_job(
            module="nautobot_golden_config.jobs", name="IntendedJob", device=Device.objects.all()
        )
        log_entries = JobLogEntry.objects.filter(job_result=job_result, grouping="Get Job Filter")
        self.assertEqual(log_entries.count(), 2)
        self.assertEqual(log_entries.last().message, "In scope device count for this job: 2")

        log_entries = JobLogEntry.objects.filter(job_result=job_result, grouping="GC Repo Syncs")
        self.assertEqual(log_entries.first().message, "Repository types to sync: ")

        log_entries = JobLogEntry.objects.filter(job_result=job_result, grouping="run")
        self.assertEqual(
            log_entries.last().message, "`E3032:` The intended feature is disabled in Golden Config settings."
        )


@patch("nautobot_golden_config.nornir_plays.config_compliance.run_compliance", MagicMock(return_value="foo"))
@patch.object(jobs, "ensure_git_repository")
class GCReposComplianceTestCase(BaseGoldenConfigTestCase):
    """Test the repos to sync and commit are working for compliance job."""

    databases = ("default", "job_logs")

    def setUp(self) -> None:
        """Setup test data."""
        self.device = create_device(name="foobaz")
        self.device2 = create_orphan_device(name="foobaz2")
        dgs_gc_settings_and_job_repo_objects()
        super().setUp()

    def test_compliance_job_repos_one_setting(self, mock_ensure_git_repository):
        """Test compliance job one GC setting enabled_compliance enabled"""
        mock_ensure_git_repository.return_value = True
        self.update_golden_config_settings(compliance_enabled=True)
        job_result = create_job_result_and_run_job(
            module="nautobot_golden_config.jobs",
            name="ComplianceJob",
            device=Device.objects.filter(name=self.device.name),
        )

        log_entries = JobLogEntry.objects.filter(job_result=job_result, grouping="GC Repo Syncs")
        self.assertEqual(
            log_entries.first().message, "Repository types to sync: backup_repository, intended_repository"
        )

        log_entries = JobLogEntry.objects.filter(job_result=job_result, grouping="Get Job Filter")
        self.assertEqual(log_entries.count(), 2)
        self.assertEqual(log_entries.last().message, "In scope device count for this job: 1")

        log_entries = JobLogEntry.objects.filter(job_result=job_result, grouping="GC After Run")
        self.assertEqual(log_entries.first().message, "Finished the Perform Configuration Compliance job execution.")

        log_entries = JobLogEntry.objects.filter(job_result=job_result, grouping="GC Repo Commit and Push")
        self.assertEqual(log_entries.count(), 1)

    def test_compliance_job_repos_two_setting(self, mock_ensure_git_repository):
        """Test compliance job two GC setting enabled_compliance enabled"""
        mock_ensure_git_repository.return_value = True
        self.update_golden_config_settings(compliance_enabled=True)
        job_result = create_job_result_and_run_job(
            module="nautobot_golden_config.jobs", name="ComplianceJob", device=Device.objects.all()
        )
        log_entries = JobLogEntry.objects.filter(job_result=job_result, grouping="Get Job Filter")
        self.assertEqual(log_entries.count(), 2)
        self.assertEqual(log_entries.last().message, "In scope device count for this job: 2")

        log_entries = JobLogEntry.objects.filter(job_result=job_result, grouping="GC Repo Syncs")
        self.assertEqual(
            log_entries.first().message, "Repository types to sync: backup_repository, intended_repository"
        )

        log_entries = JobLogEntry.objects.filter(job_result=job_result, grouping="GC After Run")
        self.assertEqual(log_entries.first().message, "Finished the Perform Configuration Compliance job execution.")

        log_entries = JobLogEntry.objects.filter(job_result=job_result, grouping="GC Repo Commit and Push")
        self.assertEqual(log_entries.count(), 1)

    def test_compliance_job_repos_one_setting_compliance_disabled(self, mock_ensure_git_repository):
        """Test compliance job one GC setting enabled_compliance disabled"""
        mock_ensure_git_repository.return_value = True
        self.update_golden_config_settings(compliance_enabled=False)
        job_result = create_job_result_and_run_job(
            module="nautobot_golden_config.jobs",
            name="ComplianceJob",
            device=Device.objects.filter(name=self.device.name),
        )
        log_entries = JobLogEntry.objects.filter(job_result=job_result, grouping="GC Repo Syncs")
        self.assertEqual(log_entries.first().message, "Repository types to sync: ")

        log_entries = JobLogEntry.objects.filter(job_result=job_result, grouping="Get Job Filter")
        self.assertEqual(log_entries.count(), 2)
        self.assertEqual(log_entries.last().message, "In scope device count for this job: 1")

        log_entries = JobLogEntry.objects.filter(job_result=job_result, grouping="run")
        self.assertEqual(
            log_entries.last().message, "`E3032:` The compliance feature is disabled in Golden Config settings."
        )

    def test_compliance_job_repos_two_setting_compliance_disabled(self, mock_ensure_git_repository):
        """Test compliance job two GC setting enabled_compliance disabled"""
        mock_ensure_git_repository.return_value = True
        self.update_golden_config_settings(compliance_enabled=False)
        job_result = create_job_result_and_run_job(
            module="nautobot_golden_config.jobs", name="ComplianceJob", device=Device.objects.all()
        )
        log_entries = JobLogEntry.objects.filter(job_result=job_result, grouping="Get Job Filter")
        self.assertEqual(log_entries.count(), 2)
        self.assertEqual(log_entries.last().message, "In scope device count for this job: 2")

        log_entries = JobLogEntry.objects.filter(job_result=job_result, grouping="GC Repo Syncs")
        self.assertEqual(log_entries.first().message, "Repository types to sync: ")

        log_entries = JobLogEntry.objects.filter(job_result=job_result, grouping="run")
        self.assertEqual(
            log_entries.last().message, "`E3032:` The compliance feature is disabled in Golden Config settings."
        )

    def test_compliance_job_repos_backup_disabled(self, mock_ensure_git_repository):
        """Test compliance job one GC setting enabled_backup disabled"""
        mock_ensure_git_repository.return_value = True
        self.update_golden_config_settings(backup_enabled=False)
        job_result = create_job_result_and_run_job(
            module="nautobot_golden_config.jobs", name="ComplianceJob", device=Device.objects.all()
        )
        log_entries = JobLogEntry.objects.filter(job_result=job_result, grouping="Get Job Filter")
        self.assertEqual(log_entries.count(), 2)
        self.assertEqual(log_entries.last().message, "In scope device count for this job: 2")

        log_entries = JobLogEntry.objects.filter(job_result=job_result, grouping="GC Repo Syncs")
        self.assertEqual(
            log_entries.first().message, "Repository types to sync: backup_repository, intended_repository"
        )

        log_entries = JobLogEntry.objects.filter(job_result=job_result, grouping="GC After Run")
        self.assertEqual(log_entries.first().message, "Finished the Perform Configuration Compliance job execution.")

        log_entries = JobLogEntry.objects.filter(job_result=job_result, grouping="GC Repo Commit and Push")
        self.assertEqual(log_entries.count(), 1)

    def test_compliance_job_repos_intended_disabled(self, mock_ensure_git_repository):
        """Test compliance job one GC setting enabled_intended disabled"""
        mock_ensure_git_repository.return_value = True
        self.update_golden_config_settings(intended_enabled=False)
        job_result = create_job_result_and_run_job(
            module="nautobot_golden_config.jobs", name="ComplianceJob", device=Device.objects.all()
        )
        log_entries = JobLogEntry.objects.filter(job_result=job_result, grouping="Get Job Filter")
        self.assertEqual(log_entries.count(), 2)
        self.assertEqual(log_entries.last().message, "In scope device count for this job: 2")
        log_entries = JobLogEntry.objects.filter(job_result=job_result, grouping="GC Repo Syncs")
        self.assertEqual(
            log_entries.first().message, "Repository types to sync: backup_repository, intended_repository"
        )

        log_entries = JobLogEntry.objects.filter(job_result=job_result, grouping="GC After Run")
        self.assertEqual(log_entries.first().message, "Finished the Perform Configuration Compliance job execution.")

        log_entries = JobLogEntry.objects.filter(job_result=job_result, grouping="GC Repo Commit and Push")
        self.assertEqual(log_entries.count(), 1)

    def test_compliance_job_repos_both_disabled(self, mock_ensure_git_repository):
        """Test compliance job one GC setting both disabled"""
        mock_ensure_git_repository.return_value = True
        self.update_golden_config_settings(backup_enabled=False, intended_enabled=False)
        job_result = create_job_result_and_run_job(
            module="nautobot_golden_config.jobs", name="ComplianceJob", device=Device.objects.all()
        )
        log_entries = JobLogEntry.objects.filter(job_result=job_result, grouping="Get Job Filter")
        self.assertEqual(log_entries.count(), 2)
        self.assertEqual(log_entries.last().message, "In scope device count for this job: 2")
        log_entries = JobLogEntry.objects.filter(job_result=job_result, grouping="GC Repo Syncs")
        self.assertEqual(
            log_entries.first().message, "Repository types to sync: backup_repository, intended_repository"
        )

        log_entries = JobLogEntry.objects.filter(job_result=job_result, grouping="GC After Run")
        self.assertEqual(log_entries.first().message, "Finished the Perform Configuration Compliance job execution.")

        log_entries = JobLogEntry.objects.filter(job_result=job_result, grouping="GC Repo Commit and Push")
        self.assertEqual(log_entries.count(), 0)


@patch("nautobot_golden_config.nornir_plays.config_backup.run_backup", MagicMock(return_value="foo"))
@patch("nautobot_golden_config.nornir_plays.config_intended.run_template", MagicMock(return_value="foo"))
@patch("nautobot_golden_config.nornir_plays.config_compliance.run_compliance", MagicMock(return_value="foo"))
@patch.object(jobs, "ensure_git_repository")
class GCReposRunAllSingleTestCase(BaseGoldenConfigTestCase):
    """Test the repos to sync and commit are working for run all single job."""

    databases = ("default", "job_logs")

    def setUp(self) -> None:
        """Setup test data."""
        self.device = create_device(name="foobaz")
        dgs_gc_settings_and_job_repo_objects()
        super().setUp()

    def test_run_all_job_single_repos(self, mock_ensure_git_repository):
        """Test run all job single on one GC setting enabled"""
        mock_ensure_git_repository.return_value = True
        self.update_golden_config_settings(
            backup_enabled=True,
            intended_enabled=True,
            compliance_enabled=True,
            deploy_enabled=True,
        )
        job_result = create_job_result_and_run_job(
            module="nautobot_golden_config.jobs", name="AllGoldenConfig", device=self.device.id
        )
        log_entries = JobLogEntry.objects.filter(job_result=job_result, grouping="GC Repo Syncs")
        self.assertEqual(
            log_entries.first().message,
            "Repository types to sync: backup_repository, intended_repository, jinja_repository",
        )

        log_entries = JobLogEntry.objects.filter(job_result=job_result, grouping="Get Job Filter")
        self.assertEqual(log_entries.count(), 2)
        self.assertEqual(log_entries.last().message, "In scope device count for this job: 1")

        log_entries = JobLogEntry.objects.filter(job_result=job_result, grouping="GC After Run")
        self.assertEqual(
            log_entries.first().message,
            "Finished the Execute All Golden Configuration Jobs - Single Device job execution.",
        )

        log_entries = JobLogEntry.objects.filter(job_result=job_result, grouping="GC Repo Commit and Push")
        self.assertEqual(log_entries.count(), 1)

    def test_run_all_job_single_repos_backup_disabled(self, mock_ensure_git_repository):
        """Test run all job single on one GC backup_disabled"""
        mock_ensure_git_repository.return_value = True
        self.update_golden_config_settings(backup_enabled=False)
        job_result = create_job_result_and_run_job(
            module="nautobot_golden_config.jobs", name="AllGoldenConfig", device=self.device.id
        )
        log_entries = JobLogEntry.objects.filter(job_result=job_result, grouping="GC Repo Syncs")
        self.assertEqual(
            log_entries.first().message,
            "Repository types to sync: backup_repository, intended_repository, jinja_repository",
        )

        log_entries = JobLogEntry.objects.filter(job_result=job_result, grouping="Get Job Filter")
        self.assertEqual(log_entries.count(), 2)
        self.assertEqual(log_entries.last().message, "In scope device count for this job: 1")

        log_entries = JobLogEntry.objects.filter(job_result=job_result, grouping="GC After Run")
        self.assertEqual(
            log_entries.first().message,
            "Finished the Execute All Golden Configuration Jobs - Single Device job execution.",
        )

        log_entries = JobLogEntry.objects.filter(job_result=job_result, grouping="GC Repo Commit and Push")
        self.assertEqual(log_entries.count(), 1)

    def test_run_all_job_single_repos_intended_disabled(self, mock_ensure_git_repository):
        """Test run all job single on one GC intended_disabled"""
        mock_ensure_git_repository.return_value = True
        self.update_golden_config_settings(intended_enabled=False)
        job_result = create_job_result_and_run_job(
            module="nautobot_golden_config.jobs", name="AllGoldenConfig", device=self.device.id
        )
        log_entries = JobLogEntry.objects.filter(job_result=job_result, grouping="GC Repo Syncs")
        self.assertEqual(
            log_entries.first().message,
            "Repository types to sync: backup_repository, intended_repository, jinja_repository",
        )

        log_entries = JobLogEntry.objects.filter(job_result=job_result, grouping="Get Job Filter")
        self.assertEqual(log_entries.count(), 2)
        self.assertEqual(log_entries.last().message, "In scope device count for this job: 1")

        log_entries = JobLogEntry.objects.filter(job_result=job_result, grouping="GC After Run")
        self.assertEqual(
            log_entries.first().message,
            "Finished the Execute All Golden Configuration Jobs - Single Device job execution.",
        )

        log_entries = JobLogEntry.objects.filter(job_result=job_result, grouping="GC Repo Commit and Push")
        self.assertEqual(log_entries.count(), 1)

    def test_run_all_job_single_repos_both_disabled(self, mock_ensure_git_repository):
        """Test run all job single on one GC both_disabled"""
        mock_ensure_git_repository.return_value = True
        self.update_golden_config_settings(backup_enabled=False, intended_enabled=False)
        job_result = create_job_result_and_run_job(
            module="nautobot_golden_config.jobs", name="AllGoldenConfig", device=self.device.id
        )
        log_entries = JobLogEntry.objects.filter(job_result=job_result, grouping="GC Repo Syncs")
        self.assertEqual(
            log_entries.first().message,
            "Repository types to sync: backup_repository, intended_repository, jinja_repository",
        )

        log_entries = JobLogEntry.objects.filter(job_result=job_result, grouping="Get Job Filter")
        self.assertEqual(log_entries.count(), 2)
        self.assertEqual(log_entries.last().message, "In scope device count for this job: 1")

        log_entries = JobLogEntry.objects.filter(job_result=job_result, grouping="GC After Run")
        self.assertEqual(
            log_entries.first().message,
            "Finished the Execute All Golden Configuration Jobs - Single Device job execution.",
        )

        log_entries = JobLogEntry.objects.filter(job_result=job_result, grouping="GC Repo Commit and Push")
        self.assertEqual(log_entries.count(), 0)


@patch("nautobot_golden_config.nornir_plays.config_backup.run_backup", MagicMock(return_value="foo"))
@patch("nautobot_golden_config.nornir_plays.config_intended.run_template", MagicMock(return_value="foo"))
@patch("nautobot_golden_config.nornir_plays.config_compliance.run_compliance", MagicMock(return_value="foo"))
@patch.object(jobs, "ensure_git_repository")
class GCReposRunAllMultipleTestCase(BaseGoldenConfigTestCase):
    """Test the repos to sync and commit are working for run all multiple job."""

    databases = ("default", "job_logs")

    def setUp(self) -> None:
        """Setup test data."""
        self.device = create_device(name="foobaz")
        self.device2 = create_orphan_device(name="foobaz2")
        dgs_gc_settings_and_job_repo_objects()
        super().setUp()

    def test_run_all_job_multiple_repos(self, mock_ensure_git_repository):
        """Test run all job multiple on one GC setting enabled"""
        mock_ensure_git_repository.return_value = True
        self.update_golden_config_settings(backup_enabled=True)
        job_result = create_job_result_and_run_job(
            module="nautobot_golden_config.jobs", name="AllDevicesGoldenConfig", device=Device.objects.all()
        )
        log_entries = JobLogEntry.objects.filter(job_result=job_result, grouping="GC Repo Syncs")
        self.assertEqual(
            log_entries.first().message,
            "Repository types to sync: backup_repository, intended_repository, jinja_repository",
        )

        log_entries = JobLogEntry.objects.filter(job_result=job_result, grouping="Get Job Filter")
        self.assertEqual(log_entries.count(), 2)
        self.assertEqual(log_entries.last().message, "In scope device count for this job: 2")

        log_entries = JobLogEntry.objects.filter(job_result=job_result, grouping="GC After Run")
        self.assertEqual(
            log_entries.first().message,
            "Finished the Execute All Golden Configuration Jobs - Multiple Device job execution.",
        )

        log_entries = JobLogEntry.objects.filter(job_result=job_result, grouping="GC Repo Commit and Push")
        self.assertEqual(log_entries.count(), 1)

    def test_run_all_job_multiple_repos_backup_disabled(self, mock_ensure_git_repository):
        """Test run all job multiple on one GC backup_disabled"""
        mock_ensure_git_repository.return_value = True
        self.update_golden_config_settings(backup_enabled=False)
        job_result = create_job_result_and_run_job(
            module="nautobot_golden_config.jobs", name="AllDevicesGoldenConfig", device=Device.objects.all()
        )
        log_entries = JobLogEntry.objects.filter(job_result=job_result, grouping="GC Repo Syncs")
        self.assertEqual(
            log_entries.first().message,
            "Repository types to sync: backup_repository, intended_repository, jinja_repository",
        )

        log_entries = JobLogEntry.objects.filter(job_result=job_result, grouping="Get Job Filter")
        self.assertEqual(log_entries.count(), 2)
        self.assertEqual(log_entries.last().message, "In scope device count for this job: 2")

        log_entries = JobLogEntry.objects.filter(job_result=job_result, grouping="GC After Run")
        self.assertEqual(
            log_entries.first().message,
            "Finished the Execute All Golden Configuration Jobs - Multiple Device job execution.",
        )

        log_entries = JobLogEntry.objects.filter(job_result=job_result, grouping="GC Repo Commit and Push")
        self.assertEqual(log_entries.count(), 1)

    def test_run_all_job_multiple_repos_intended_disabled(self, mock_ensure_git_repository):
        """Test run all job multiple on one GC intended_disabled"""
        mock_ensure_git_repository.return_value = True
        self.update_golden_config_settings(intended_enabled=True)
        job_result = create_job_result_and_run_job(
            module="nautobot_golden_config.jobs", name="AllDevicesGoldenConfig", device=Device.objects.all()
        )
        log_entries = JobLogEntry.objects.filter(job_result=job_result, grouping="GC Repo Syncs")
        self.assertEqual(
            log_entries.first().message,
            "Repository types to sync: backup_repository, intended_repository, jinja_repository",
        )

        log_entries = JobLogEntry.objects.filter(job_result=job_result, grouping="Get Job Filter")
        self.assertEqual(log_entries.count(), 2)
        self.assertEqual(log_entries.last().message, "In scope device count for this job: 2")

        log_entries = JobLogEntry.objects.filter(job_result=job_result, grouping="GC After Run")
        self.assertEqual(
            log_entries.first().message,
            "Finished the Execute All Golden Configuration Jobs - Multiple Device job execution.",
        )

        log_entries = JobLogEntry.objects.filter(job_result=job_result, grouping="GC Repo Commit and Push")
        self.assertEqual(log_entries.count(), 1)

    def test_run_all_job_multiple_repos_both_disabled(self, mock_ensure_git_repository):
        """Test run all job multiple on one GC both_disabled"""
        mock_ensure_git_repository.return_value = True
        self.update_golden_config_settings(backup_enabled=False, intended_enabled=False)
        job_result = create_job_result_and_run_job(
            module="nautobot_golden_config.jobs", name="AllDevicesGoldenConfig", device=Device.objects.all()
        )
        log_entries = JobLogEntry.objects.filter(job_result=job_result, grouping="GC Repo Syncs")
        self.assertEqual(
            log_entries.first().message,
            "Repository types to sync: backup_repository, intended_repository, jinja_repository",
        )

        log_entries = JobLogEntry.objects.filter(job_result=job_result, grouping="Get Job Filter")
        self.assertEqual(log_entries.count(), 2)
        self.assertEqual(log_entries.last().message, "In scope device count for this job: 2")

        log_entries = JobLogEntry.objects.filter(job_result=job_result, grouping="GC After Run")
        self.assertEqual(
            log_entries.first().message,
            "Finished the Execute All Golden Configuration Jobs - Multiple Device job execution.",
        )

        log_entries = JobLogEntry.objects.filter(job_result=job_result, grouping="GC Repo Commit and Push")
        self.assertEqual(log_entries.count(), 0)
