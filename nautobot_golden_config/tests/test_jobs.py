"""Basic Job Test."""
from unittest.mock import patch, MagicMock
from nautobot.apps.testing import TransactionTestCase, run_job_for_testing
from nautobot.extras.models import Job, JobLogEntry
from nautobot.dcim.models import Device
from nautobot_golden_config.tests.conftest import (
    create_device,
    create_orphan_device,
    dgs_gc_settings_and_job_repo_objects,
)


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

    def test_backup_job_repos_one_setting(self, mock_ensure_git_repository):
        """Test backup job repo-types are backup only."""
        mock_ensure_git_repository.return_value = True
        job = Job.objects.get_for_class_path("nautobot_golden_config.jobs.BackupJob")
        job_result = run_job_for_testing(job, device=Device.objects.all())

        log_entries = JobLogEntry.objects.filter(job_result=job_result, grouping="GC Repo Syncs")
        self.assertEqual(log_entries.first().message, "Repository types to sync: backup_repository")
