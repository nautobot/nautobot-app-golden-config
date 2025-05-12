"""Jobs to run backups, intended config, and compliance."""
# pylint: disable=too-many-function-args

from datetime import datetime

from nautobot.dcim.models import Device, DeviceRole, DeviceType, Manufacturer, Platform, Rack, RackGroup, Region, Site
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
from nautobot.extras.models import DynamicGroup, GitRepository, Status, Tag
from nautobot.tenancy.models import Tenant, TenantGroup
from nornir_nautobot.exceptions import NornirNautobotException

from nautobot_golden_config.choices import ConfigPlanTypeChoice
from nautobot_golden_config.models import ComplianceFeature, ConfigPlan
from nautobot_golden_config.nornir_plays.config_backup import config_backup
from nautobot_golden_config.nornir_plays.config_compliance import config_compliance
from nautobot_golden_config.nornir_plays.config_deployment import config_deployment
from nautobot_golden_config.nornir_plays.config_intended import config_intended
from nautobot_golden_config.utilities import constant
from nautobot_golden_config.utilities.config_plan import (
    config_plan_default_status,
    generate_config_set_from_compliance_feature,
    generate_config_set_from_manual,
)
from nautobot_golden_config.utilities.git import GitRepo
from nautobot_golden_config.utilities.helper import get_job_filter

name = "Golden Configuration"  # pylint: disable=invalid-name


def get_refreshed_repos(job_obj, repo_type, data=None):  # pylint: disable=unused-argument
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
        ensure_git_repository(repo)
        git_repo = GitRepo(repo)
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
        has_sensitive_variables = False

    @commit_check
    def run(self, data, commit):  # pylint: disable=too-many-branches
        """Run config compliance report script."""
        # pylint: disable=unused-argument
        self.log_debug("Starting compliance job.")

        self.log_debug("Refreshing intended configuration git repository.")
        get_refreshed_repos(job_obj=self, repo_type="intended_repository", data=data)
        self.log_debug("Refreshing backup configuration git repository.")
        get_refreshed_repos(job_obj=self, repo_type="backup_repository", data=data)

        self.log_debug("Starting config compliance nornir play.")
        config_compliance(self, data)


class IntendedJob(Job, FormEntry):
    """Job to to run generation of intended configurations."""

    class Meta:
        """Meta object boilerplate for intended."""

        name = "Generate Intended Configurations"
        description = "Generate the configuration for your intended state."
        has_sensitive_variables = False

    @commit_check
    def run(self, data, commit):
        """Run config generation script."""
        self.log_debug("Starting intended job.")

        now = datetime.now()

        self.log_debug("Pull Jinja template repos.")
        get_refreshed_repos(job_obj=self, repo_type="jinja_repository", data=data)

        self.log_debug("Pull Intended config repos.")
        # Instantiate a GitRepo object for each GitRepository in GoldenConfigSettings.
        intended_repos = get_refreshed_repos(job_obj=self, repo_type="intended_repository", data=data)

        self.log_debug("Building device settings mapping and running intended config nornir play.")
        config_intended(self, data)

        # Commit / Push each repo after job is completed.
        for intended_repo in intended_repos:
            self.log_debug(f"{intended_repo.obj.name}: repo updated")

            self.log_debug(f"Push new intended config to repo {intended_repo.obj.name}.")
            intended_repo.commit_with_added(f"INTENDED CONFIG CREATION JOB - {now}")
            intended_repo.push()


class BackupJob(Job, FormEntry):
    """Job to to run the backup job."""

    class Meta:
        """Meta object boilerplate for backup configurations."""

        name = "Backup Configurations"
        description = "Backup the configurations of your network devices."
        has_sensitive_variables = False

    @commit_check
    def run(self, data, commit):
        """Run config backup process."""
        self.log_debug("Starting backup job.")
        now = datetime.now()
        self.log_debug("Pull Backup config repo.")

        # Instantiate a GitRepo object for each GitRepository in GoldenConfigSettings.
        backup_repos = get_refreshed_repos(job_obj=self, repo_type="backup_repository", data=data)

        self.log_debug(f"Starting backup jobs to the following repos: {backup_repos}")

        self.log_debug("Starting config backup nornir play.")
        config_backup(self, data)

        # Commit / Push each repo after job is completed.
        for backup_repo in backup_repos:
            self.log_debug(f"Pushing Backup config to repo {backup_repo.obj.name}")
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
        has_sensitive_variables = False

    @commit_check
    def run(self, data, commit):
        """Run all jobs."""
        if constant.ENABLE_INTENDED:
            IntendedJob().run.__func__(self, data, True)  # pylint: disable=too-many-function-args
        if constant.ENABLE_BACKUP:
            BackupJob().run.__func__(self, data, True)  # pylint: disable=too-many-function-args
        if constant.ENABLE_COMPLIANCE:
            ComplianceJob().run.__func__(self, data, True)  # pylint: disable=too-many-function-args


class AllDevicesGoldenConfig(Job, FormEntry):
    """Job to to run all three jobs against multiple devices."""

    class Meta:
        """Meta object boilerplate for all jobs to run against multiple devices."""

        name = "Execute All Golden Configuration Jobs - Multiple Device"
        description = "Process to run all Golden Configuration jobs configured against multiple devices."
        has_sensitive_variables = False

    @commit_check
    def run(self, data, commit):
        """Run all jobs."""
        if constant.ENABLE_INTENDED:
            IntendedJob().run.__func__(self, data, True)  # pylint: disable=too-many-function-args
        if constant.ENABLE_BACKUP:
            BackupJob().run.__func__(self, data, True)  # pylint: disable=too-many-function-args
        if constant.ENABLE_COMPLIANCE:
            ComplianceJob().run.__func__(self, data, True)  # pylint: disable=too-many-function-args


class GenerateConfigPlans(Job, FormEntry):
    """Job to generate config plans."""

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
        has_sensitive_variables = False
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
                self.log_failure("No commands entered for config plan generation.")
                return False
        return True

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
                self.log_debug(f"Device `{device}` does not have `{self._plan_type}` configs for `{_features}`.")
                continue
            config_plan = ConfigPlan.objects.create(
                device=device,
                plan_type=self._plan_type,
                config_set="\n".join(config_sets),
                change_control_id=self._change_control_id,
                change_control_url=self._change_control_url,
                status=self._status,
                plan_result=self.job_result,
            )
            config_plan.feature.set(features)
            config_plan.validated_save()
            _features = ", ".join([str(feat) for feat in features])
            self.log_success(obj=config_plan, message=f"Config plan created for `{device}` with feature `{_features}`.")

    def _generate_config_plan_from_manual(self):
        """Generate config plans from manual."""
        default_context = {
            "request": self.request,
            "user": self.request.user,
        }
        for device in self._device_qs:
            config_set = generate_config_set_from_manual(device, self._commands, context=default_context)
            if not config_set:
                self.log_debug(f"Device {self.device} did not return a rendered config set from the provided commands.")
                continue
            config_plan = ConfigPlan.objects.create(
                device=device,
                plan_type=self._plan_type,
                config_set=config_set,
                change_control_id=self._change_control_id,
                change_control_url=self._change_control_url,
                status=self._status,
                plan_result=self.job_result,
            )
            self.log_success(obj=config_plan, message=f"Config plan created for {device} with manual commands.")

    def run(self, data, commit):
        """Run config plan generation process."""
        self.log_debug("Starting config plan generation job.")
        if not self._validate_inputs(data):
            return
        try:
            self._device_qs = get_job_filter(data)
        except NornirNautobotException as exc:
            self.log_failure(str(exc))
            return
        if self._plan_type in ["intended", "missing", "remediation"]:
            self.log_debug("Starting config plan generation for compliance features.")
            self._generate_config_plan_from_feature()
        elif self._plan_type in ["manual"]:
            self.log_debug("Starting config plan generation for manual commands.")
            self._generate_config_plan_from_manual()
        else:
            self.log_failure(f"Unknown config plan type {self._plan_type}.")
            return


class DeployConfigPlans(Job):
    """Job to deploy config plans."""

    config_plan = MultiObjectVar(model=ConfigPlan, required=True)
    debug = BooleanVar(description="Enable for more verbose debug logging")

    class Meta:
        """Meta object boilerplate for config plan deployment."""

        name = "Deploy Config Plans"
        description = "Deploy config plans to devices."
        has_sensitive_variables = False

    def run(self, data, commit):
        """Run config plan deployment process."""
        self.log_debug("Starting config plan deployment job.")
        config_deployment(self, data, commit)


class DeployConfigPlanJobButtonReceiver(JobButtonReceiver):
    """Job button to deploy a config plan."""

    class Meta:
        """Meta object boilerplate for config plan deployment job button."""

        name = "Deploy Config Plan (Job Button Receiver)"
        has_sensitive_variables = False

    def receive_job_button(self, obj):
        """Run config plan deployment process."""
        self.log_debug("Starting config plan deployment job.")
        data = {"debug": False, "config_plan": ConfigPlan.objects.filter(id=obj.id)}
        config_deployment(self, data, commit=True)


# Conditionally allow jobs based on whether or not turned on.
jobs = []
if constant.ENABLE_BACKUP:
    jobs.append(BackupJob)
if constant.ENABLE_INTENDED:
    jobs.append(IntendedJob)
if constant.ENABLE_COMPLIANCE:
    jobs.append(ComplianceJob)
if constant.ENABLE_PLAN:
    jobs.append(GenerateConfigPlans)
if constant.ENABLE_DEPLOY:
    jobs.append(DeployConfigPlans)
    jobs.append(DeployConfigPlanJobButtonReceiver)
jobs.extend(
    [
        AllGoldenConfig,
        AllDevicesGoldenConfig,
    ]
)
