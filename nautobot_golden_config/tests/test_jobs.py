"""Basic Job Test."""
from unittest.mock import patch, MagicMock
from nautobot.apps.testing import TransactionTestCase
from nautobot.extras.models import Job
from nautobot.dcim.models import Device
from nautobot_golden_config.tests.conftest import (
    create_git_repos,
    create_device,
    create_orphan_device,
    dgs_gc_settings_and_job_repo_objects,
)
from nautobot_golden_config.utilities import constant
from nautobot_golden_config.jobs import get_refreshed_repos


class DefaultRepoTypesTestCase(TransactionTestCase):
    """Test a job that default Repo_Types are Set properly."""

    databases = ("default", "job_logs")

    def setUp(self) -> None:
        """Setup test data."""
        create_git_repos()
        super().setUp()

    def test_backup_job_repo_types(self):
        """Test backup job repo-types are backup only."""
        job = Job.objects.get_for_class_path("nautobot_golden_config.jobs.BackupJob")
        self.assertEqual(job.job_task.Meta.repo_types, ["backup_repository"])

    def test_backup_job_repos(self):
        """Test backup job repos."""
        job = Job.objects.get_for_class_path("nautobot_golden_config.jobs.BackupJob")
        self.assertEqual(job.job_task.Meta.repo_types, ["backup_repository"])

    def test_intended_job_repo_types(self):
        """Test intended job repo-types are accurate."""
        job = Job.objects.get_for_class_path("nautobot_golden_config.jobs.IntendedJob")
        self.assertEqual(job.job_task.Meta.repo_types, ["jinja_repository", "intended_repository"])

    def test_compliance_job_repo_types(self):
        """Test compliance job repo-types are accurate"""
        job = Job.objects.get_for_class_path("nautobot_golden_config.jobs.ComplianceJob")
        self.assertEqual(job.job_task.Meta.repo_types, ["intended_repository", "backup_repository"])

    def test_run_all_single_job_repo_types(self):
        """Test run-all-single job repo-types are accurate."""
        job = Job.objects.get_for_class_path("nautobot_golden_config.jobs.AllGoldenConfig")
        # Should be empty as all repo_types get defined by settings.
        self.assertEqual(job.job_task.Meta.repo_types, [])

    def test_run_all_multiple_job_repo_types(self):
        """Test run-all-multiple job repo-types are accurate."""
        job = Job.objects.get_for_class_path("nautobot_golden_config.jobs.AllDevicesGoldenConfig")
        # Should be empty as all repo_types get defined by settings.
        self.assertEqual(job.job_task.Meta.repo_types, [])


@patch("nautobot_golden_config.nornir_plays.config_backup.run_backup", MagicMock(return_value="foo"))
@patch("nautobot_golden_config.jobs.ensure_git_repository")
class GCReposBackupTestCase(TransactionTestCase):
    """Test the repos to sync and commit are working for backup job."""

    databases = ("default", "job_logs")

    def setUp(self) -> None:
        """Setup test data."""
        self.device = create_device(name="foobaz")
        self.device2 = create_orphan_device(name="foobaz2")
        dgs_gc_settings_and_job_repo_objects()
        super().setUp()

    def test_get_refreshed_repos_backup_only_sync_one_setting(self, mock_ensure_git_repository):
        """Test refreshed repos single GC setting."""
        mock_ensure_git_repository.return_value = True
        job_obj = MagicMock()
        job_obj.logger = MagicMock()
        backup_repositories = get_refreshed_repos(
            job_obj, "backup_repository", data={"device": Device.objects.get(name=self.device.name)}
        )
        self.assertTrue(constant.ENABLE_BACKUP)
        self.assertEqual(len(backup_repositories), 1)

    @patch("nautobot_golden_config.utilities.constant.ENABLE_BACKUP", False)
    def test_get_refreshed_repos_backup_only_sync_one_setting_backup_disabled(self, mock_ensure_git_repository):
        """Test refreshed repos single GC setting backup disabled."""
        mock_ensure_git_repository.return_value = True
        job_obj = MagicMock()
        job_obj.logger = MagicMock()
        backup_repositories = get_refreshed_repos(
            job_obj, "backup_repository", data={"device": Device.objects.get(name=self.device.name)}
        )
        self.assertFalse(constant.ENABLE_BACKUP)
        self.assertEqual(len(backup_repositories), 1)

    def test_get_refreshed_repos_backup_only_sync_two_setting(self, mock_ensure_git_repository):
        """Test refreshed repos multiple GC setting."""
        mock_ensure_git_repository.return_value = True
        job_obj = MagicMock()
        job_obj.logger = MagicMock()
        backup_repositories = get_refreshed_repos(job_obj, "backup_repository", data={"device": Device.objects.all()})
        self.assertTrue(constant.ENABLE_BACKUP)
        self.assertEqual(len(backup_repositories), 2)

    @patch("nautobot_golden_config.utilities.constant.ENABLE_BACKUP", False)
    def test_get_refreshed_repos_backup_only_sync_two_setting_backup_disabled(self, mock_ensure_git_repository):
        """Test refreshed repos multiple GC setting."""
        mock_ensure_git_repository.return_value = True
        job_obj = MagicMock()
        job_obj.logger = MagicMock()
        backup_repositories = get_refreshed_repos(job_obj, "backup_repository", data={"device": Device.objects.all()})
        self.assertFalse(constant.ENABLE_BACKUP)
        self.assertEqual(len(backup_repositories), 2)

    def test_get_refreshed_repos_backup_to_commit(self, mock_ensure_git_repository):
        """Test whicgh repos should be commited multiple GC setting backups enabled."""
        mock_ensure_git_repository.return_value = True
        job_obj = MagicMock()
        job_obj.logger = MagicMock()
        backup_repositories = get_refreshed_repos(job_obj, "backup_repository", data={"device": Device.objects.all()})
        self.assertTrue(constant.ENABLE_BACKUP)
        self.assertTrue(backup_repositories[0].to_commit)
        self.assertTrue(backup_repositories[1].to_commit)

    @patch("nautobot_golden_config.utilities.constant.ENABLE_BACKUP", False)
    def test_get_refreshed_repos_backup_to_commit_backup_disabled(self, mock_ensure_git_repository):
        """Test whicgh repos should be commited multiple GC setting backups disabled."""
        mock_ensure_git_repository.return_value = True
        job_obj = MagicMock()
        job_obj.logger = MagicMock()
        backup_repositories = get_refreshed_repos(job_obj, "backup_repository", data={"device": Device.objects.all()})
        self.assertFalse(constant.ENABLE_BACKUP)
        self.assertFalse(backup_repositories[0].to_commit)
        self.assertFalse(backup_repositories[1].to_commit)


@patch("nautobot_golden_config.nornir_plays.config_intended.run_template", MagicMock(return_value="foo"))
@patch("nautobot_golden_config.jobs.ensure_git_repository")
class GCReposIntendedTestCase(TransactionTestCase):
    """Test the repos to sync and commit are working for intended job."""

    databases = ("default", "job_logs")

    def setUp(self) -> None:
        """Setup test data."""
        self.device = create_device(name="foobaz")
        self.device2 = create_orphan_device(name="foobaz2")
        dgs_gc_settings_and_job_repo_objects()
        super().setUp()

    def test_get_refreshed_repos_intended_only_sync_one_setting(self, mock_ensure_git_repository):
        """Test refreshed repos single GC setting."""
        mock_ensure_git_repository.return_value = True
        job_obj = MagicMock()
        job_obj.logger = MagicMock()
        intended_repositories = get_refreshed_repos(
            job_obj, "intended_repository", data={"device": Device.objects.get(name=self.device.name)}
        )
        self.assertTrue(constant.ENABLE_INTENDED)
        self.assertEqual(len(intended_repositories), 1)
        template_repositories = get_refreshed_repos(
            job_obj, "jinja_repository", data={"device": Device.objects.get(name=self.device.name)}
        )
        self.assertEqual(len(template_repositories), 1)

    @patch("nautobot_golden_config.utilities.constant.ENABLE_INTENDED", False)
    def test_get_refreshed_repos_intended_only_sync_one_setting_intended_disabled(self, mock_ensure_git_repository):
        """Test refreshed repos single GC setting intended disabled."""
        mock_ensure_git_repository.return_value = True
        job_obj = MagicMock()
        job_obj.logger = MagicMock()
        intended_repositories = get_refreshed_repos(
            job_obj, "intended_repository", data={"device": Device.objects.get(name=self.device.name)}
        )
        self.assertFalse(constant.ENABLE_INTENDED)
        self.assertEqual(len(intended_repositories), 1)
        template_repositories = get_refreshed_repos(
            job_obj, "jinja_repository", data={"device": Device.objects.get(name=self.device.name)}
        )
        self.assertEqual(len(template_repositories), 1)

    def test_get_refreshed_repos_intended_only_sync_two_setting(self, mock_ensure_git_repository):
        """Test refreshed repos multiple GC setting."""
        mock_ensure_git_repository.return_value = True
        job_obj = MagicMock()
        job_obj.logger = MagicMock()
        intended_repositories = get_refreshed_repos(
            job_obj, "intended_repository", data={"device": Device.objects.all()}
        )
        self.assertTrue(constant.ENABLE_INTENDED)
        self.assertEqual(len(intended_repositories), 2)
        template_repositories = get_refreshed_repos(job_obj, "jinja_repository", data={"device": Device.objects.all()})
        self.assertEqual(len(template_repositories), 1)

    @patch("nautobot_golden_config.utilities.constant.ENABLE_INTENDED", False)
    def test_get_refreshed_repos_intended_only_sync_two_setting_intended_disabled(self, mock_ensure_git_repository):
        """Test refreshed repos multiple GC setting."""
        mock_ensure_git_repository.return_value = True
        job_obj = MagicMock()
        job_obj.logger = MagicMock()
        intended_repositories = get_refreshed_repos(
            job_obj, "intended_repository", data={"device": Device.objects.all()}
        )
        self.assertFalse(constant.ENABLE_INTENDED)
        self.assertEqual(len(intended_repositories), 2)
        template_repositories = get_refreshed_repos(job_obj, "jinja_repository", data={"device": Device.objects.all()})
        self.assertEqual(len(template_repositories), 1)

    def test_get_refreshed_repos_intended_to_commit(self, mock_ensure_git_repository):
        """Test whicgh repos should be commited multiple GC setting intendeds enabled."""
        mock_ensure_git_repository.return_value = True
        job_obj = MagicMock()
        job_obj.logger = MagicMock()
        intended_repositories = get_refreshed_repos(
            job_obj, "intended_repository", data={"device": Device.objects.all()}
        )
        self.assertTrue(constant.ENABLE_INTENDED)
        self.assertTrue(intended_repositories[0].to_commit)
        self.assertTrue(intended_repositories[1].to_commit)

    @patch("nautobot_golden_config.utilities.constant.ENABLE_INTENDED", False)
    def test_get_refreshed_repos_intended_to_commit_intended_disabled(self, mock_ensure_git_repository):
        """Test whicgh repos should be commited multiple GC setting intendeds disabled."""
        mock_ensure_git_repository.return_value = True
        job_obj = MagicMock()
        job_obj.logger = MagicMock()
        intended_repositories = get_refreshed_repos(
            job_obj, "intended_repository", data={"device": Device.objects.all()}
        )
        self.assertFalse(constant.ENABLE_INTENDED)
        self.assertFalse(intended_repositories[0].to_commit)
        self.assertFalse(intended_repositories[1].to_commit)

    # @patch("nautobot_golden_config.nornir_plays.config_backup.run_backup", MagicMock(return_value="foo"))
    # def test_backup_job_repos(self):
    #     """Test backup job repo-types are backup only."""
    #     job = Job.objects.get_for_class_path("nautobot_golden_config.jobs.BackupJob")
    #     job_result = run_job_for_testing(job, device=Device.objects.all())

    #     log_entries = JobLogEntry.objects.filter(job_result=job_result, grouping="GC Repo Syncs")
    #     self.assertEqual(log_entries.first().message, "Repository types to sync: backup_repository")


@patch("nautobot_golden_config.nornir_plays.config_compliance.run_compliance", MagicMock(return_value="foo"))
@patch("nautobot_golden_config.jobs.ensure_git_repository")
class GCReposComplianceTestCase(TransactionTestCase):
    """Test the repos to sync and commit are working for compliance job."""

    databases = ("default", "job_logs")

    def setUp(self) -> None:
        """Setup test data."""
        self.device = create_device(name="foobaz")
        self.device2 = create_orphan_device(name="foobaz2")
        dgs_gc_settings_and_job_repo_objects()
        super().setUp()

    def test_get_refreshed_repos_compliance_only_sync_one_setting(self, mock_ensure_git_repository):
        """Test refreshed repos single GC setting."""
        mock_ensure_git_repository.return_value = True
        job_obj = MagicMock()
        job_obj.logger = MagicMock()
        backup_repositories = get_refreshed_repos(
            job_obj, "backup_repository", data={"device": Device.objects.get(name=self.device.name)}
        )
        self.assertTrue(constant.ENABLE_INTENDED)
        self.assertEqual(len(backup_repositories), 1)
        intended_repositories = get_refreshed_repos(
            job_obj, "intended_repository", data={"device": Device.objects.get(name=self.device.name)}
        )
        self.assertEqual(len(intended_repositories), 1)

    @patch("nautobot_golden_config.utilities.constant.ENABLE_INTENDED", False)
    def test_get_refreshed_repos_compliance_only_sync_one_setting_compliance_disabled(self, mock_ensure_git_repository):
        """Test refreshed repos single GC setting intended disabled."""
        mock_ensure_git_repository.return_value = True
        job_obj = MagicMock()
        job_obj.logger = MagicMock()
        backup_repositories = get_refreshed_repos(
            job_obj, "backup_repository", data={"device": Device.objects.get(name=self.device.name)}
        )
        self.assertFalse(constant.ENABLE_INTENDED)
        self.assertEqual(len(backup_repositories), 1)
        intended_repositories = get_refreshed_repos(
            job_obj, "intended_repository", data={"device": Device.objects.get(name=self.device.name)}
        )
        self.assertEqual(len(intended_repositories), 1)

    def test_get_refreshed_repos_compliance_only_sync_two_setting(self, mock_ensure_git_repository):
        """Test refreshed repos multiple GC setting."""
        mock_ensure_git_repository.return_value = True
        job_obj = MagicMock()
        job_obj.logger = MagicMock()
        backup_repositories = get_refreshed_repos(job_obj, "backup_repository", data={"device": Device.objects.all()})
        self.assertTrue(constant.ENABLE_INTENDED)
        self.assertEqual(len(backup_repositories), 2)
        intended_repositories = get_refreshed_repos(
            job_obj, "intended_repository", data={"device": Device.objects.all()}
        )
        self.assertEqual(len(intended_repositories), 2)

    @patch("nautobot_golden_config.utilities.constant.ENABLE_INTENDED", False)
    def test_get_refreshed_repos_compliance_only_sync_two_setting_compliance_disabled(self, mock_ensure_git_repository):
        """Test refreshed repos multiple GC setting."""
        mock_ensure_git_repository.return_value = True
        job_obj = MagicMock()
        job_obj.logger = MagicMock()
        backup_repositories = get_refreshed_repos(job_obj, "backup_repository", data={"device": Device.objects.all()})
        self.assertFalse(constant.ENABLE_INTENDED)
        self.assertEqual(len(backup_repositories), 2)
        intended_repositories = get_refreshed_repos(
            job_obj, "intended_repository", data={"device": Device.objects.all()}
        )
        self.assertEqual(len(intended_repositories), 2)

    def test_get_refreshed_repos_compliance_to_commit(self, mock_ensure_git_repository):
        """Test whicgh repos should be commited multiple GC setting intendeds enabled."""
        mock_ensure_git_repository.return_value = True
        job_obj = MagicMock()
        job_obj.logger = MagicMock()
        backup_repositories = get_refreshed_repos(job_obj, "backup_repository", data={"device": Device.objects.all()})
        self.assertTrue(constant.ENABLE_INTENDED)
        self.assertTrue(backup_repositories[0].to_commit)
        self.assertTrue(backup_repositories[1].to_commit)
        intended_repositories = get_refreshed_repos(
            job_obj, "intended_repository", data={"device": Device.objects.all()}
        )
        self.assertEqual(len(intended_repositories), 2)
        self.assertTrue(intended_repositories[0].to_commit)
        self.assertTrue(intended_repositories[1].to_commit)

    @patch("nautobot_golden_config.utilities.constant.ENABLE_INTENDED", False)
    @patch("nautobot_golden_config.utilities.constant.ENABLE_BACKUP", False)
    def test_get_refreshed_repos_compliance_to_commit_both_disabled(self, mock_ensure_git_repository):
        """Test whicgh repos should be commited multiple GC setting intendeds disabled."""
        mock_ensure_git_repository.return_value = True
        job_obj = MagicMock()
        job_obj.logger = MagicMock()
        backup_repositories = get_refreshed_repos(job_obj, "backup_repository", data={"device": Device.objects.all()})
        self.assertFalse(constant.ENABLE_INTENDED)
        self.assertFalse(constant.ENABLE_BACKUP)
        self.assertFalse(backup_repositories[0].to_commit)
        self.assertFalse(backup_repositories[1].to_commit)
        intended_repositories = get_refreshed_repos(
            job_obj, "intended_repository", data={"device": Device.objects.all()}
        )
        self.assertEqual(len(intended_repositories), 2)
        self.assertFalse(intended_repositories[0].to_commit)
        self.assertFalse(intended_repositories[1].to_commit)


@patch("nautobot_golden_config.nornir_plays.config_backup.run_backup", MagicMock(return_value="backup_foo"))
@patch("nautobot_golden_config.nornir_plays.config_intended.run_template", MagicMock(return_value="template_foo"))
@patch("nautobot_golden_config.nornir_plays.config_compliance.run_compliance", MagicMock(return_value="compliance_foo"))
@patch("nautobot_golden_config.jobs.ensure_git_repository")
class GCReposRunAllTestCase(TransactionTestCase):
    """Test the repos to sync and commit are working for compliance job."""

    databases = ("default", "job_logs")

    def setUp(self) -> None:
        """Setup test data."""
        self.device = create_device(name="foobaz")
        self.device2 = create_orphan_device(name="foobaz2")
        dgs_gc_settings_and_job_repo_objects()
        super().setUp()

    def test_get_refreshed_repos_run_all_settings_true(self, mock_ensure_git_repository):
        """Test refreshed repos backups true intended true."""
        mock_ensure_git_repository.return_value = True
        job_obj = MagicMock()
        job_obj.logger = MagicMock()
        self.assertTrue(constant.ENABLE_INTENDED)
        self.assertTrue(constant.ENABLE_BACKUP)
        backup_repositories = get_refreshed_repos(job_obj, "backup_repository", data={"device": Device.objects.all()})
        self.assertEqual(len(backup_repositories), 2)
        self.assertTrue(backup_repositories[0].to_commit)
        self.assertTrue(backup_repositories[1].to_commit)
        intended_repositories = get_refreshed_repos(
            job_obj, "intended_repository", data={"device": Device.objects.all()}
        )
        self.assertEqual(len(intended_repositories), 2)
        self.assertTrue(intended_repositories[0].to_commit)
        self.assertTrue(intended_repositories[1].to_commit)
        template_repositories = get_refreshed_repos(job_obj, "jinja_repository", data={"device": Device.objects.all()})
        self.assertEqual(len(template_repositories), 1)
        self.assertFalse(template_repositories[0].to_commit)

    @patch("nautobot_golden_config.utilities.constant.ENABLE_INTENDED", False)
    def test_get_refreshed_repos_run_backup_true_intended_false(self, mock_ensure_git_repository):
        """Test refreshed repos backups true intended false."""
        mock_ensure_git_repository.return_value = True
        job_obj = MagicMock()
        job_obj.logger = MagicMock()
        self.assertFalse(constant.ENABLE_INTENDED)
        self.assertTrue(constant.ENABLE_BACKUP)
        backup_repositories = get_refreshed_repos(job_obj, "backup_repository", data={"device": Device.objects.all()})
        self.assertEqual(len(backup_repositories), 2)
        self.assertTrue(backup_repositories[0].to_commit)
        self.assertTrue(backup_repositories[1].to_commit)
        intended_repositories = get_refreshed_repos(
            job_obj, "intended_repository", data={"device": Device.objects.all()}
        )
        self.assertEqual(len(intended_repositories), 2)
        self.assertFalse(intended_repositories[0].to_commit)
        self.assertFalse(intended_repositories[1].to_commit)
        template_repositories = get_refreshed_repos(job_obj, "jinja_repository", data={"device": Device.objects.all()})
        self.assertEqual(len(template_repositories), 1)
        self.assertFalse(template_repositories[0].to_commit)

    @patch("nautobot_golden_config.utilities.constant.ENABLE_BACKUP", False)
    def test_get_refreshed_repos_run_backup_false_intended_true(self, mock_ensure_git_repository):
        """Test refreshed repos backups true intended false."""
        mock_ensure_git_repository.return_value = True
        job_obj = MagicMock()
        job_obj.logger = MagicMock()
        self.assertTrue(constant.ENABLE_INTENDED)
        self.assertFalse(constant.ENABLE_BACKUP)
        backup_repositories = get_refreshed_repos(job_obj, "backup_repository", data={"device": Device.objects.all()})
        self.assertEqual(len(backup_repositories), 2)
        self.assertFalse(backup_repositories[0].to_commit)
        self.assertFalse(backup_repositories[1].to_commit)
        intended_repositories = get_refreshed_repos(
            job_obj, "intended_repository", data={"device": Device.objects.all()}
        )
        self.assertEqual(len(intended_repositories), 2)
        self.assertTrue(intended_repositories[0].to_commit)
        self.assertTrue(intended_repositories[1].to_commit)
        template_repositories = get_refreshed_repos(job_obj, "jinja_repository", data={"device": Device.objects.all()})
        self.assertEqual(len(template_repositories), 1)
        self.assertFalse(template_repositories[0].to_commit)

    @patch("nautobot_golden_config.utilities.constant.ENABLE_BACKUP", False)
    @patch("nautobot_golden_config.utilities.constant.ENABLE_INTENDED", False)
    def test_get_refreshed_repos_run_backup_false_intended_false(self, mock_ensure_git_repository):
        """Test refreshed repos backups true intended false."""
        mock_ensure_git_repository.return_value = True
        job_obj = MagicMock()
        job_obj.logger = MagicMock()
        self.assertFalse(constant.ENABLE_INTENDED)
        self.assertFalse(constant.ENABLE_BACKUP)
        backup_repositories = get_refreshed_repos(job_obj, "backup_repository", data={"device": Device.objects.all()})
        self.assertEqual(len(backup_repositories), 2)
        self.assertFalse(backup_repositories[0].to_commit)
        self.assertFalse(backup_repositories[1].to_commit)
        intended_repositories = get_refreshed_repos(
            job_obj, "intended_repository", data={"device": Device.objects.all()}
        )
        self.assertEqual(len(intended_repositories), 2)
        self.assertFalse(intended_repositories[0].to_commit)
        self.assertFalse(intended_repositories[1].to_commit)
        template_repositories = get_refreshed_repos(job_obj, "jinja_repository", data={"device": Device.objects.all()})
        self.assertEqual(len(template_repositories), 1)
        self.assertFalse(template_repositories[0].to_commit)
