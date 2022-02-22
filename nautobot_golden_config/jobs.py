"""Jobs to run backups, intended config, and compliance."""
import logging

from datetime import datetime

from nautobot.extras.jobs import Job, MultiObjectVar, ObjectVar, BooleanVar
from nautobot.extras.models import Tag
from nautobot.extras.datasources.git import ensure_git_repository
from nautobot.dcim.models import Device, DeviceRole, DeviceType, Manufacturer, Site, Platform, Region, Rack, RackGroup
from nautobot.tenancy.models import Tenant, TenantGroup

from nautobot_golden_config.models import GoldenConfigSetting
from nautobot_golden_config.nornir_plays.config_intended import config_intended
from nautobot_golden_config.nornir_plays.config_backup import config_backup
from nautobot_golden_config.nornir_plays.config_compliance import config_compliance
from nautobot_golden_config.utilities.constant import ENABLE_BACKUP, ENABLE_COMPLIANCE, ENABLE_INTENDED
from nautobot_golden_config.utilities.git import GitRepo

LOGGER = logging.getLogger(__name__)


name = "Golden Configuration"  # pylint: disable=invalid-name


def get_refreshed_repos(job_obj, repo_type):
    """Small wrapper to pull latest branch, and return a GitRepo plugin specific object."""
    repository_records = set(
        getattr(gcs, repo_type) for gcs in GoldenConfigSetting.objects.all() if getattr(gcs, repo_type, None)
    )

    repositories = []
    for repository_record in repository_records:
        ensure_git_repository(repository_record, job_obj.job_result)
        git_repo = GitRepo(repository_record)
        repositories.append(git_repo)

    return repositories


def commit_check(method):
    """Decorator to check if a "dry-run" attempt was made."""

    def inner(obj, data, commit):
        """Decorator bolierplate code."""
        msg = "Dry-run mode is not supported, please set the commit flag to proceed."
        if not commit:
            raise ValueError(msg)
        return method(obj, data, commit)

    return inner


class FormEntry:  # pylint disable=too-few-public-method
    """Class definition to use as Mixin for form definitions."""

    tenant_group = MultiObjectVar(model=TenantGroup, required=False)
    tenant = MultiObjectVar(model=Tenant, required=False)
    region = MultiObjectVar(model=Region, required=False)
    site = MultiObjectVar(model=Site, required=False)
    rack_group = MultiObjectVar(model=RackGroup, required=False)
    rack = MultiObjectVar(model=Rack, required=False)
    role = MultiObjectVar(model=DeviceRole, required=False)
    manufacturer = MultiObjectVar(model=Manufacturer, required=False)
    platform = MultiObjectVar(model=Platform, required=False)
    device_type = MultiObjectVar(model=DeviceType, required=False, display_field="display_name")
    device = MultiObjectVar(model=Device, required=False)
    tag = MultiObjectVar(model=Tag, required=False)
    debug = BooleanVar(description="Enable for more verbose debug logging")
    # TODO: Add status


class ComplianceJob(Job, FormEntry):
    """Job to to run the compliance engine."""

    tenant_group = FormEntry.tenant_group
    tenant = FormEntry.tenant
    region = FormEntry.region
    site = FormEntry.site
    rack_group = FormEntry.rack_group
    rack = FormEntry.rack
    role = FormEntry.role
    manufacturer = FormEntry.manufacturer
    platform = FormEntry.platform
    device_type = FormEntry.device_type
    device = FormEntry.device
    tag = FormEntry.tag
    debug = FormEntry.debug

    class Meta:
        """Meta object boilerplate for compliance."""

        name = "Perform Configuration Compliance"
        description = "Run configuration compliance on your network infrastructure."

    @commit_check
    def run(self, data, commit):  # pylint: disable=too-many-branches
        """Run config compliance report script."""
        # pylint: disable=unused-argument

        get_refreshed_repos(job_obj=self, repo_type="intended_repository")
        get_refreshed_repos(job_obj=self, repo_type="backup_repository")

        config_compliance(self, data)


class IntendedJob(Job, FormEntry):
    """Job to to run generation of intended configurations."""

    tenant_group = FormEntry.tenant_group
    tenant = FormEntry.tenant
    region = FormEntry.region
    site = FormEntry.site
    rack_group = FormEntry.rack_group
    rack = FormEntry.rack
    role = FormEntry.role
    manufacturer = FormEntry.manufacturer
    platform = FormEntry.platform
    device_type = FormEntry.device_type
    device = FormEntry.device
    tag = FormEntry.tag
    debug = FormEntry.debug

    class Meta:
        """Meta object boilerplate for intended."""

        name = "Generate Intended Configurations"
        description = "Generate the configuration for your intended state."

    @commit_check
    def run(self, data, commit):
        """Run config generation script."""
        now = datetime.now()

        LOGGER.debug("Pull Jinja template repos.")
        get_refreshed_repos(job_obj=self, repo_type="jinja_repository")

        LOGGER.debug("Pull Intended config repos.")
        # Instantiate a GitRepo object for each GitRepository in GoldenConfigSettings.
        intended_repos = get_refreshed_repos(job_obj=self, repo_type="intended_repository")

        LOGGER.debug("Run config intended nornir play.")
        config_intended(self, data)

        # Commit / Push each repo after job is completed.
        for intended_repo in intended_repos:
            LOGGER.debug("Push new intended configs to repo %s.", intended_repo.url)
            intended_repo.commit_with_added(f"INTENDED CONFIG CREATION JOB - {now}")
            intended_repo.push()


class BackupJob(Job, FormEntry):
    """Job to to run the backup job."""

    tenant_group = FormEntry.tenant_group
    tenant = FormEntry.tenant
    region = FormEntry.region
    site = FormEntry.site
    rack_group = FormEntry.rack_group
    rack = FormEntry.rack
    role = FormEntry.role
    manufacturer = FormEntry.manufacturer
    platform = FormEntry.platform
    device_type = FormEntry.device_type
    device = FormEntry.device
    tag = FormEntry.tag
    debug = FormEntry.debug

    class Meta:
        """Meta object boilerplate for backup configurations."""

        name = "Backup Configurations"
        description = "Backup the configurations of your network devices."

    @commit_check
    def run(self, data, commit):
        """Run config backup process."""
        now = datetime.now()
        LOGGER.debug("Pull Backup config repo.")

        # Instantiate a GitRepo object for each GitRepository in GoldenConfigSettings.
        backup_repos = get_refreshed_repos(job_obj=self, repo_type="backup_repository")

        LOGGER.debug("Starting backup jobs to the following repos: %s", backup_repos)

        LOGGER.debug("Run nornir play.")
        config_backup(self, data)

        # Commit / Push each repo after job is completed.
        for backup_repo in backup_repos:
            LOGGER.debug("Pushing Backup config repo %s.", backup_repo.url)
            backup_repo.commit_with_added(f"BACKUP JOB {now}")
            backup_repo.push()


class AllGoldenConfig(Job):
    """Job to to run all three jobs against a single device."""

    device = ObjectVar(model=Device, required=True)
    debug = BooleanVar(description="Enable for more verbose debug logging")

    class Meta:
        """Meta object boilerplate for all jobs to run against a device."""

        name = "Execute All Golden Configuration Jobs - Single Device"
        description = "Process to run all Golden Configuration jobs configured."

    @commit_check
    def run(self, data, commit):
        """Run all jobs."""
        if ENABLE_INTENDED:
            IntendedJob().run.__func__(self, data, True)
        if ENABLE_BACKUP:
            BackupJob().run.__func__(self, data, True)
        if ENABLE_COMPLIANCE:
            ComplianceJob().run.__func__(self, data, True)


class AllDevicesGoldenConfig(Job):
    """Job to to run all three jobs against multiple devices."""

    tenant_group = FormEntry.tenant_group
    tenant = FormEntry.tenant
    region = FormEntry.region
    site = FormEntry.site
    rack_group = FormEntry.rack_group
    rack = FormEntry.rack
    role = FormEntry.role
    manufacturer = FormEntry.manufacturer
    platform = FormEntry.platform
    device_type = FormEntry.device_type
    device = FormEntry.device
    tag = FormEntry.tag
    debug = FormEntry.debug

    class Meta:
        """Meta object boilerplate for all jobs to run against multiple devices."""

        name = "Execute All Golden Configuration Jobs - Multiple Device"
        description = "Process to run all Golden Configuration jobs configured against multiple devices."

    @commit_check
    def run(self, data, commit):
        """Run all jobs."""
        if ENABLE_INTENDED:
            IntendedJob().run.__func__(self, data, True)
        if ENABLE_BACKUP:
            BackupJob().run.__func__(self, data, True)
        if ENABLE_COMPLIANCE:
            ComplianceJob().run.__func__(self, data, True)


# Conditionally allow jobs based on whether or not turned on.
jobs = []
if ENABLE_BACKUP:
    jobs.append(BackupJob)
if ENABLE_INTENDED:
    jobs.append(IntendedJob)
if ENABLE_COMPLIANCE:
    jobs.append(ComplianceJob)
jobs.extend([AllGoldenConfig, AllDevicesGoldenConfig])
