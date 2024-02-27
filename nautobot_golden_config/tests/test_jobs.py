"""Basic Job Test."""

from nautobot.apps.testing import TransactionTestCase
from nautobot.extras.models import Job
from nautobot_golden_config.tests.conftest import create_git_repos


class RepoTypesTestCase(TransactionTestCase):
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
