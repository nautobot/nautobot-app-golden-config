"""Basic Job Test."""
from unittest.mock import patch, MagicMock
from django.contrib.contenttypes.models import ContentType
from nautobot.apps.testing import TransactionTestCase
from nautobot.extras.models import Job
from nautobot.extras.models import GitRepository, GraphQLQuery, DynamicGroup
from nautobot.dcim.models import Device
from nautobot_golden_config.tests.conftest import (
    create_git_repos,
    create_device,
    create_saved_queries,
    create_orphan_device,
)
from nautobot_golden_config.utilities import constant
from nautobot_golden_config.jobs import get_refreshed_repos
from nautobot_golden_config.models import GoldenConfigSetting


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
        create_git_repos()
        create_saved_queries()
        # Since we enforce a singleton pattern on this model, nuke the auto-created object.
        GoldenConfigSetting.objects.all().delete()

        dynamic_group1 = DynamicGroup.objects.create(
            name="dg foobaz",
            content_type=ContentType.objects.get_for_model(Device),
            filter={"platform": ["Platform 1"]},
        )
        dynamic_group2 = DynamicGroup.objects.create(
            name="dg foobaz2",
            content_type=ContentType.objects.get_for_model(Device),
            filter={"platform": ["Platform 4"]},
        )

        GoldenConfigSetting.objects.create(
            name="test_name",
            slug="test_slug",
            weight=1000,
            description="Test Description.",
            backup_path_template="test/backup",
            intended_path_template="test/intended",
            jinja_path_template="{{jinja_path}}",
            backup_test_connectivity=True,
            dynamic_group=dynamic_group1,
            sot_agg_query=GraphQLQuery.objects.get(name="GC-SoTAgg-Query-1"),
            backup_repository=GitRepository.objects.filter(
                provided_contents__contains="nautobot_golden_config.backupconfigs"
            ).first(),
            intended_repository=GitRepository.objects.filter(
                provided_contents__contains="nautobot_golden_config.intendedconfigs"
            ).first(),
            jinja_repository=GitRepository.objects.filter(
                provided_contents__contains="nautobot_golden_config.jinjatemplate"
            ).first(),
        )
        GoldenConfigSetting.objects.create(
            name="test_name2",
            slug="test_slug2",
            weight=1000,
            description="Test Description.",
            backup_path_template="test/backup",
            intended_path_template="test/intended",
            jinja_path_template="{{jinja_path}}",
            backup_test_connectivity=True,
            dynamic_group=dynamic_group2,
            sot_agg_query=GraphQLQuery.objects.get(name="GC-SoTAgg-Query-1"),
            backup_repository=GitRepository.objects.filter(
                provided_contents__contains="nautobot_golden_config.backupconfigs"
            ).last(),
            intended_repository=GitRepository.objects.filter(
                provided_contents__contains="nautobot_golden_config.intendedconfigs"
            ).last(),
            jinja_repository=GitRepository.objects.filter(
                provided_contents__contains="nautobot_golden_config.jinjatemplate"
            ).last(),
        )
        super().setUp()

    def test_get_refreshed_repos_backup_only_sync_one_setting(self, mock_ensure_git_repository):
        """Test refreshed repos single GC setting."""
        mock_ensure_git_repository.return_value = True
        job_obj = MagicMock()
        job_obj.logger = MagicMock()
        repositories = get_refreshed_repos(
            job_obj, "backup_repository", data={"device": Device.objects.get(name=self.device.name)}
        )
        self.assertTrue(constant.ENABLE_BACKUP)
        self.assertEqual(len(repositories), 1)

    @patch("nautobot_golden_config.utilities.constant.ENABLE_BACKUP", False)
    def test_get_refreshed_repos_backup_only_sync_one_setting_backup_disabled(self, mock_ensure_git_repository):
        """Test refreshed repos single GC setting backup disabled."""
        mock_ensure_git_repository.return_value = True
        job_obj = MagicMock()
        job_obj.logger = MagicMock()
        repositories = get_refreshed_repos(
            job_obj, "backup_repository", data={"device": Device.objects.get(name=self.device.name)}
        )
        self.assertFalse(constant.ENABLE_BACKUP)
        self.assertEqual(len(repositories), 1)

    def test_get_refreshed_repos_backup_only_sync_two_setting(self, mock_ensure_git_repository):
        """Test refreshed repos multiple GC setting."""
        mock_ensure_git_repository.return_value = True
        job_obj = MagicMock()
        job_obj.logger = MagicMock()
        repositories = get_refreshed_repos(job_obj, "backup_repository", data={"device": Device.objects.all()})
        self.assertTrue(constant.ENABLE_BACKUP)
        self.assertEqual(len(repositories), 2)

    @patch("nautobot_golden_config.utilities.constant.ENABLE_BACKUP", False)
    def test_get_refreshed_repos_backup_only_sync_two_setting_backup_disabled(self, mock_ensure_git_repository):
        """Test refreshed repos multiple GC setting."""
        mock_ensure_git_repository.return_value = True
        job_obj = MagicMock()
        job_obj.logger = MagicMock()
        repositories = get_refreshed_repos(job_obj, "backup_repository", data={"device": Device.objects.all()})
        self.assertFalse(constant.ENABLE_BACKUP)
        self.assertEqual(len(repositories), 2)

    def test_get_refreshed_repos_backup_to_commit(self, mock_ensure_git_repository):
        """Test whicgh repos should be commited multiple GC setting backups enabled."""
        mock_ensure_git_repository.return_value = True
        job_obj = MagicMock()
        job_obj.logger = MagicMock()
        repositories = get_refreshed_repos(job_obj, "backup_repository", data={"device": Device.objects.all()})
        self.assertTrue(constant.ENABLE_BACKUP)
        self.assertTrue(repositories[0].to_commit)
        self.assertTrue(repositories[1].to_commit)

    @patch("nautobot_golden_config.utilities.constant.ENABLE_BACKUP", False)
    def test_get_refreshed_repos_backup_to_commit_backup_disabled(self, mock_ensure_git_repository):
        """Test whicgh repos should be commited multiple GC setting backups disabled."""
        mock_ensure_git_repository.return_value = True
        job_obj = MagicMock()
        job_obj.logger = MagicMock()
        repositories = get_refreshed_repos(job_obj, "backup_repository", data={"device": Device.objects.all()})
        self.assertFalse(constant.ENABLE_BACKUP)
        self.assertFalse(repositories[0].to_commit)
        self.assertFalse(repositories[1].to_commit)


@patch("nautobot_golden_config.nornir_plays.config_intended.run_template", MagicMock(return_value="foo"))
@patch("nautobot_golden_config.jobs.ensure_git_repository")
class GCReposIntendedTestCase(TransactionTestCase):
    """Test the repos to sync and commit are working for intended job."""

    databases = ("default", "job_logs")

    def setUp(self) -> None:
        """Setup test data."""
        self.device = create_device(name="foobaz")
        self.device2 = create_orphan_device(name="foobaz2")
        create_git_repos()
        create_saved_queries()
        # Since we enforce a singleton pattern on this model, nuke the auto-created object.
        GoldenConfigSetting.objects.all().delete()

        dynamic_group1 = DynamicGroup.objects.create(
            name="dg foobaz",
            content_type=ContentType.objects.get_for_model(Device),
            filter={"platform": ["Platform 1"]},
        )
        dynamic_group2 = DynamicGroup.objects.create(
            name="dg foobaz2",
            content_type=ContentType.objects.get_for_model(Device),
            filter={"platform": ["Platform 4"]},
        )

        GoldenConfigSetting.objects.create(
            name="test_name",
            slug="test_slug",
            weight=1000,
            description="Test Description.",
            backup_path_template="test/backup",
            intended_path_template="test/intended",
            jinja_path_template="{{jinja_path}}",
            backup_test_connectivity=True,
            dynamic_group=dynamic_group1,
            sot_agg_query=GraphQLQuery.objects.get(name="GC-SoTAgg-Query-1"),
            backup_repository=GitRepository.objects.filter(
                provided_contents__contains="nautobot_golden_config.backupconfigs"
            ).first(),
            intended_repository=GitRepository.objects.filter(
                provided_contents__contains="nautobot_golden_config.intendedconfigs"
            ).first(),
            jinja_repository=GitRepository.objects.filter(
                provided_contents__contains="nautobot_golden_config.jinjatemplate"
            ).first(),
        )
        GoldenConfigSetting.objects.create(
            name="test_name2",
            slug="test_slug2",
            weight=1000,
            description="Test Description.",
            backup_path_template="test/backup",
            intended_path_template="test/intended",
            jinja_path_template="{{jinja_path}}",
            backup_test_connectivity=True,
            dynamic_group=dynamic_group2,
            sot_agg_query=GraphQLQuery.objects.get(name="GC-SoTAgg-Query-1"),
            backup_repository=GitRepository.objects.filter(
                provided_contents__contains="nautobot_golden_config.backupconfigs"
            ).last(),
            intended_repository=GitRepository.objects.filter(
                provided_contents__contains="nautobot_golden_config.intendedconfigs"
            ).last(),
            jinja_repository=GitRepository.objects.filter(
                provided_contents__contains="nautobot_golden_config.jinjatemplate"
            ).last(),
        )
        super().setUp()

    def test_get_refreshed_repos_intended_only_sync_one_setting(self, mock_ensure_git_repository):
        """Test refreshed repos single GC setting."""
        mock_ensure_git_repository.return_value = True
        job_obj = MagicMock()
        job_obj.logger = MagicMock()
        repositories = get_refreshed_repos(
            job_obj, "intended_repository", data={"device": Device.objects.get(name=self.device.name)}
        )
        self.assertTrue(constant.ENABLE_INTENDED)
        self.assertEqual(len(repositories), 1)

    @patch("nautobot_golden_config.utilities.constant.ENABLE_INTENDED", False)
    def test_get_refreshed_repos_intended_only_sync_one_setting_intended_disabled(self, mock_ensure_git_repository):
        """Test refreshed repos single GC setting intended disabled."""
        mock_ensure_git_repository.return_value = True
        job_obj = MagicMock()
        job_obj.logger = MagicMock()
        repositories = get_refreshed_repos(
            job_obj, "intended_repository", data={"device": Device.objects.get(name=self.device.name)}
        )
        self.assertFalse(constant.ENABLE_INTENDED)
        self.assertEqual(len(repositories), 1)

    def test_get_refreshed_repos_intended_only_sync_two_setting(self, mock_ensure_git_repository):
        """Test refreshed repos multiple GC setting."""
        mock_ensure_git_repository.return_value = True
        job_obj = MagicMock()
        job_obj.logger = MagicMock()
        repositories = get_refreshed_repos(job_obj, "intended_repository", data={"device": Device.objects.all()})
        self.assertTrue(constant.ENABLE_INTENDED)
        self.assertEqual(len(repositories), 2)

    @patch("nautobot_golden_config.utilities.constant.ENABLE_INTENDED", False)
    def test_get_refreshed_repos_intended_only_sync_two_setting_intended_disabled(self, mock_ensure_git_repository):
        """Test refreshed repos multiple GC setting."""
        mock_ensure_git_repository.return_value = True
        job_obj = MagicMock()
        job_obj.logger = MagicMock()
        repositories = get_refreshed_repos(job_obj, "intended_repository", data={"device": Device.objects.all()})
        self.assertFalse(constant.ENABLE_INTENDED)
        self.assertEqual(len(repositories), 2)

    def test_get_refreshed_repos_intended_to_commit(self, mock_ensure_git_repository):
        """Test whicgh repos should be commited multiple GC setting intendeds enabled."""
        mock_ensure_git_repository.return_value = True
        job_obj = MagicMock()
        job_obj.logger = MagicMock()
        repositories = get_refreshed_repos(job_obj, "intended_repository", data={"device": Device.objects.all()})
        self.assertTrue(constant.ENABLE_INTENDED)
        self.assertTrue(repositories[0].to_commit)
        self.assertTrue(repositories[1].to_commit)

    @patch("nautobot_golden_config.utilities.constant.ENABLE_INTENDED", False)
    def test_get_refreshed_repos_intended_to_commit_intended_disabled(self, mock_ensure_git_repository):
        """Test whicgh repos should be commited multiple GC setting intendeds disabled."""
        mock_ensure_git_repository.return_value = True
        job_obj = MagicMock()
        job_obj.logger = MagicMock()
        repositories = get_refreshed_repos(job_obj, "intended_repository", data={"device": Device.objects.all()})
        self.assertFalse(constant.ENABLE_INTENDED)
        self.assertFalse(repositories[0].to_commit)
        self.assertFalse(repositories[1].to_commit)

    # @patch("nautobot_golden_config.nornir_plays.config_backup.run_backup", MagicMock(return_value="foo"))
    # def test_backup_job_repos(self):
    #     """Test backup job repo-types are backup only."""
    #     job = Job.objects.get_for_class_path("nautobot_golden_config.jobs.BackupJob")
    #     job_result = run_job_for_testing(job, device=Device.objects.all())

    #     log_entries = JobLogEntry.objects.filter(job_result=job_result, grouping="GC Repo Syncs")
    #     self.assertEqual(log_entries.first().message, "Repository types to sync: backup_repository")
