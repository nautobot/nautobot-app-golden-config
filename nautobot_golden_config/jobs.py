"""Jobs to run backups, intended config, and compliance."""
# pylint: disable=too-many-function-args,logging-fstring-interpolation
# TODO: Remove the following ignore, added to be able to pass pylint in CI.
# pylint: disable=arguments-differ

from datetime import datetime

from nautobot.core.celery import register_jobs
from nautobot.dcim.models import Device, DeviceType, Manufacturer, Platform, Rack, RackGroup, Location
from nautobot.extras.datasources.git import ensure_git_repository
from nautobot.extras.jobs import (
    BooleanVar,
    ChoiceVar,
    Job,
    JobButtonReceiver,
    MultiObjectVar,
    ObjectVar,
    StringVar,
    TextVar,
)
from nautobot.extras.models import DynamicGroup, GitRepository, Status, Tag, Role
from nautobot.tenancy.models import Tenant, TenantGroup

from nornir_nautobot.exceptions import NornirNautobotException

from nautobot_golden_config.choices import ConfigPlanTypeChoice
from nautobot_golden_config.models import ComplianceFeature, ConfigPlan
from nautobot_golden_config.nornir_plays.config_backup import config_backup
from nautobot_golden_config.nornir_plays.config_compliance import config_compliance
from nautobot_golden_config.nornir_plays.config_deployment import config_deployment
from nautobot_golden_config.nornir_plays.config_intended import config_intended
from nautobot_golden_config.utilities.config_plan import (
    config_plan_default_status,
    generate_config_set_from_compliance_feature,
    generate_config_set_from_manual,
)
from nautobot_golden_config.utilities.constant import (
    ENABLE_BACKUP,
    ENABLE_COMPLIANCE,
    ENABLE_INTENDED,
)
from nautobot_golden_config.utilities.git import GitRepo
from nautobot_golden_config.utilities.helper import get_job_filter

name = "Golden Configuration"  # pylint: disable=invalid-name


def get_refreshed_repos(job_obj, repo_type, data=None):
    """Small wrapper to pull latest branch, and return a GitRepo plugin specific object."""
    devices = get_job_filter(data)
    dynamic_groups = DynamicGroup.objects.exclude(golden_config_setting__isnull=True)
    repository_records = set()
    # Iterate through DynamicGroups then apply the DG's filter to the devices filtered by job.
    for group in dynamic_groups:
        repo = getattr(group.golden_config_setting, repo_type, None)
        if repo and devices.filter(group.generate_query()).exists():
            repository_records.add(repo.id)

    repositories = []
    for repository_record in repository_records:
        repo = GitRepository.objects.get(id=repository_record)
        ensure_git_repository(repo, job_obj.logger)
        git_repo = GitRepo(repo)
        repositories.append(git_repo)

    return repositories


# TODO: 2.0: Does changing region/site to location affect nornir jobs?


class FormEntry:  # pylint disable=too-few-public-method
    """Class definition to use as Mixin for form definitions."""

    tenant_group = MultiObjectVar(model=TenantGroup, required=False)
    tenant = MultiObjectVar(model=Tenant, required=False)
    location = MultiObjectVar(model=Location, required=False)
    rack_group = MultiObjectVar(model=RackGroup, required=False)
    rack = MultiObjectVar(model=Rack, required=False)
    role = MultiObjectVar(model=Role, required=False)  # TODO: 2.0: How does change to Role model affect this?
    manufacturer = MultiObjectVar(model=Manufacturer, required=False)
    platform = MultiObjectVar(model=Platform, required=False)
    device_type = MultiObjectVar(model=DeviceType, required=False, display_field="display_name")
    device = MultiObjectVar(model=Device, required=False)
    tag = MultiObjectVar(model=Tag, required=False)
    status = MultiObjectVar(
        model=Status,
        required=False,
        query_params={"content_types": Device._meta.label_lower},
        display_field="label",
        label="Device Status",
    )
    debug = BooleanVar(description="Enable for more verbose debug logging")


class ComplianceJob(Job, FormEntry):
    """Job to to run the compliance engine."""

    class Meta:
        """Meta object boilerplate for compliance."""

        name = "Perform Configuration Compliance"
        description = "Run configuration compliance on your network infrastructure."

    def run(self, *args, **data):
        """Run config compliance report script."""
        self.logger.debug("Starting compliance job.")
        self.logger.debug("Refreshing intended configuration git repository.")
        get_refreshed_repos(job_obj=self, repo_type="intended_repository", data=data)
        self.logger.debug("Refreshing backup configuration git repository.")
        get_refreshed_repos(job_obj=self, repo_type="backup_repository", data=data)

        self.logger.debug("Starting config compliance nornir play.")
        config_compliance(self, data)


class IntendedJob(Job, FormEntry):
    """Job to to run generation of intended configurations."""

    class Meta:
        """Meta object boilerplate for intended."""

        name = "Generate Intended Configurations"
        description = "Generate the configuration for your intended state."

    def run(self, *args, **data):
        """Run config generation script."""
        self.logger.debug("Starting intended job.")
        now = datetime.now()
        self.logger.debug("Pull Jinja template repos.")
        get_refreshed_repos(job_obj=self, repo_type="jinja_repository", data=data)

        self.logger.debug("Pull Intended config repos.")
        # Instantiate a GitRepo object for each GitRepository in GoldenConfigSettings.
        intended_repos = get_refreshed_repos(job_obj=self, repo_type="intended_repository", data=data)

        self.logger.debug(
            "Building device settings mapping and running intended config nornir play."
        )
        config_intended(self, data)

        # Commit / Push each repo after job is completed.
        for intended_repo in intended_repos:
            self.logger.debug("Push new intended configs to repo %s.", intended_repo.url)
            intended_repo.commit_with_added(f"INTENDED CONFIG CREATION JOB - {now}")
            intended_repo.push()


class BackupJob(Job, FormEntry):
    """Job to to run the backup job."""

    class Meta:
        """Meta object boilerplate for backup configurations."""

        name = "Backup Configurations"
        description = "Backup the configurations of your network devices."

    def run(self, *args, **data):
        """Run config backup process."""
        self.logger.debug("Starting backup job.")
        now = datetime.now()
        self.logger.debug("Pull Backup config repo.")

        # Instantiate a GitRepo object for each GitRepository in GoldenConfigSettings.
        backup_repos = get_refreshed_repos(job_obj=self, repo_type="backup_repository", data=data)

        self.logger.debug("Starting backup jobs to the following repos: %s", backup_repos)
        self.logger.debug("Starting config backup nornir play.")
        config_backup(self, data)

        # Commit / Push each repo after job is completed.
        for backup_repo in backup_repos:
            self.logger.debug("Pushing Backup config repo %s.", backup_repo.url)
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

    def run(self, *args, **data):
        """Run all jobs."""
        if ENABLE_INTENDED:
            IntendedJob().run.__func__(self, data, True)
        if ENABLE_BACKUP:
            BackupJob().run.__func__(self, data, True)
        if ENABLE_COMPLIANCE:
            ComplianceJob().run.__func__(self, data, True)


class AllDevicesGoldenConfig(Job):
    """Job to to run all three jobs against multiple devices."""

    class Meta:
        """Meta object boilerplate for all jobs to run against multiple devices."""

        name = "Execute All Golden Configuration Jobs - Multiple Device"
        description = "Process to run all Golden Configuration jobs configured against multiple devices."

    def run(self, *args, **data):
        """Run all jobs."""
        if ENABLE_INTENDED:
            IntendedJob().run.__func__(self, data, True)
        if ENABLE_BACKUP:
            BackupJob().run.__func__(self, data, True)
        if ENABLE_COMPLIANCE:
            ComplianceJob().run.__func__(self, data, True)


class GenerateConfigPlans(Job, FormEntry):
    """Job to generate config plans."""

    # Device QS Filters
    tenant_group = FormEntry.tenant_group
    tenant = FormEntry.tenant
    location = FormEntry.location
    rack_group = FormEntry.rack_group
    rack = FormEntry.rack
    role = FormEntry.role
    manufacturer = FormEntry.manufacturer
    platform = FormEntry.platform
    device_type = FormEntry.device_type
    device = FormEntry.device
    tag = FormEntry.tag
    status = FormEntry.status
    debug = FormEntry.debug

    # Config Plan generation fields
    plan_type = ChoiceVar(choices=ConfigPlanTypeChoice.CHOICES)
    feature = MultiObjectVar(model=ComplianceFeature, required=False)
    change_control_id = StringVar(required=False)
    change_control_url = StringVar(required=False)
    commands = TextVar(required=False)

    class Meta:
        """Meta object boilerplate for config plan generation."""

        name = "Generate Config Plans"
        description = "Generate config plans for devices."
        # Defaulting to hidden as this should be primarily called by the View
        hidden = True

    def __init__(self, *args, **kwargs):
        """Initialize the job."""
        super().__init__(*args, **kwargs)
        self._plan_type = None
        self._feature = None
        self._change_control_id = None
        self._change_control_url = None
        self._commands = None
        self._device_qs = Device.objects.none()
        self._status = config_plan_default_status()

    def _validate_inputs(self, data):
        self._plan_type = data["plan_type"]
        self._feature = data.get("feature", [])
        self._change_control_id = data.get("change_control_id", "")
        self._change_control_url = data.get("change_control_url", "")
        self._commands = data.get("commands", "")
        if self._plan_type in ["intended", "missing", "remediation"]:
            if not self._feature:
                self._feature = ComplianceFeature.objects.all()
        if self._plan_type in ["manual"]:
            if not self._commands:
                error_msg = "No commands entered for config plan generation."
                self.logger.error(error_msg)
                raise ValueError(error_msg)

    def _generate_config_plan_from_feature(self):
        """Generate config plans from features."""
        for device in self._device_qs:
            config_sets = []
            features = []
            for feature in self._feature:
                config_set = generate_config_set_from_compliance_feature(device, self._plan_type, feature)
                if not config_set:
                    continue
                config_sets.append(config_set)
                features.append(feature)

            if not config_sets:
                _features = ", ".join([str(feat) for feat in self._feature])
                self.logger.debug(f"Device `{device}` does not have `{self._plan_type}` configs for `{_features}`.")
                continue
            config_plan = ConfigPlan.objects.create(
                device=device,
                plan_type=self._plan_type,
                config_set="\n".join(config_sets),
                change_control_id=self._change_control_id,
                change_control_url=self._change_control_url,
                status=self._status,
                job_result=self.job_result,
            )
            config_plan.feature.set(features)
            config_plan.validated_save()
            _features = ", ".join([str(feat) for feat in features])
            self.logger.info(obj=config_plan, message=f"Config plan created for `{device}` with feature `{_features}`.")

    def _generate_config_plan_from_manual(self):
        """Generate config plans from manual."""
        default_context = {
            "request": self.request,
            "user": self.user,
        }
        for device in self._device_qs:
            config_set = generate_config_set_from_manual(device, self._commands, context=default_context)
            if not config_set:
                self.logger.debug(
                    f"Device {self.device} did not return a rendered config set from the provided commands."
                )
                continue
            config_plan = ConfigPlan.objects.create(
                device=device,
                plan_type=self._plan_type,
                config_set=config_set,
                change_control_id=self._change_control_id,
                change_control_url=self._change_control_url,
                status=self._status,
                job_result=self.job_result,
            )
            self.logger.info(obj=config_plan, message=f"Config plan created for {device} with manual commands.")

    def run(self, **data):
        """Run config plan generation process."""
        self.logger.debug("Starting config plan generation job.")
        self._validate_inputs(data)
        try:
            self._device_qs = get_job_filter(data)
        except NornirNautobotException as error:
            error_msg = str(error)
            self.logger.error(error_msg)
            raise NornirNautobotException(error_msg) from error
        if self._plan_type in ["intended", "missing", "remediation"]:
            self.logger.debug("Starting config plan generation for compliance features.")
            self._generate_config_plan_from_feature()
        elif self._plan_type in ["manual"]:
            self.logger.debug("Starting config plan generation for manual commands.")
            self._generate_config_plan_from_manual()
        else:
            error_msg = f"Unknown config plan type {self._plan_type}."
            self.logger.error()
            raise ValueError(error_msg)


class DeployConfigPlans(Job):
    """Job to deploy config plans."""

    config_plan = MultiObjectVar(model=ConfigPlan, required=True)
    debug = BooleanVar(description="Enable for more verbose debug logging")

    class Meta:
        """Meta object boilerplate for config plan deployment."""

        name = "Deploy Config Plans"
        description = "Deploy config plans to devices."

    def run(self, **data):  # pylint: disable=arguments-differ
        """Run config plan deployment process."""
        self.logger.debug("Starting config plan deployment job.")
        config_deployment(self, **data)


class DeployConfigPlanJobButtonReceiver(JobButtonReceiver):
    """Job button to deploy a config plan."""

    class Meta:
        """Meta object boilerplate for config plan deployment job button."""

        name = "Deploy Config Plan (Job Button Receiver)"

    def receive_job_button(self, obj):
        """Run config plan deployment process."""
        self.logger.debug("Starting config plan deployment job.")
        data = {"debug": False, "config_plan": ConfigPlan.objects.filter(id=obj.id)}
        # pylint: disable-next=unexpected-keyword-arg
        config_deployment(self, **data)


# Conditionally allow jobs based on whether or not turned on.
if ENABLE_BACKUP:
    register_jobs(BackupJob)
if ENABLE_INTENDED:
    register_jobs(IntendedJob)
if ENABLE_COMPLIANCE:
    register_jobs(ComplianceJob)
register_jobs(GenerateConfigPlans)
register_jobs(DeployConfigPlans)
register_jobs(DeployConfigPlanJobButtonReceiver)
register_jobs(AllGoldenConfig)
register_jobs(AllDevicesGoldenConfig)
