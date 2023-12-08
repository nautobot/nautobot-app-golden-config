"""Jobs to run backups, intended config, and compliance."""
# pylint: disable=too-many-function-args,logging-fstring-interpolation
# TODO: Remove the following ignore, added to be able to pass pylint in CI.
# pylint: disable=arguments-differ

from datetime import datetime

from django.utils.timezone import make_aware
from nautobot.core.celery import register_jobs
from nautobot.dcim.models import Device, DeviceType, Location, Manufacturer, Platform, Rack, RackGroup
from nautobot.extras.datasources.git import ensure_git_repository, get_repo_from_url_to_path_and_from_branch
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
from nautobot.extras.models import DynamicGroup, GitRepository, Role, Status, Tag
from nautobot.tenancy.models import Tenant, TenantGroup
from nornir_nautobot.exceptions import NornirNautobotException
from nautobot_golden_config.choices import ConfigPlanTypeChoice
from nautobot_golden_config.models import ComplianceFeature, ConfigPlan, GoldenConfig
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
        # TODO: Should this not point to non-nautobot.core import
        # We should ask in nautobot core for the `from_url` constructor to be it's own function
        git_info = get_repo_from_url_to_path_and_from_branch(repo)
        git_repo = GitRepo(repo.filesystem_path, git_info.from_url, clone_initially=False, base_url=repo.remote_url)
        repositories.append(git_repo)

    return repositories


class FormEntry:  # pylint disable=too-few-public-method
    """Class definition to use as Mixin for form definitions."""

    tenant_group = MultiObjectVar(model=TenantGroup, required=False)
    tenant = MultiObjectVar(model=Tenant, required=False)
    location = MultiObjectVar(model=Location, required=False)
    rack_group = MultiObjectVar(model=RackGroup, required=False)
    rack = MultiObjectVar(model=Rack, required=False)
    role = MultiObjectVar(model=Role, required=False)
    manufacturer = MultiObjectVar(model=Manufacturer, required=False)
    platform = MultiObjectVar(model=Platform, required=False)
    device_type = MultiObjectVar(model=DeviceType, required=False, display_field="display_name")
    device = MultiObjectVar(model=Device, required=False)
    tags = MultiObjectVar(
        model=Tag, required=False, display_field="name", query_params={"content_types": "dcim.device"}
    )
    status = MultiObjectVar(
        model=Status,
        required=False,
        query_params={"content_types": Device._meta.label_lower},
        display_field="label",
        label="Device Status",
    )
    debug = BooleanVar(description="Enable for more verbose debug logging")


class GoldenConfigJobMixin(Job):  # pylint: disable=abstract-method
    """Reused mixin to be able to reuse common celery primitives in all GC jobs."""

    def before_start(self, task_id, args, kwargs):
        """Ensure repos before tasks runs."""
        super().before_start(task_id, args, kwargs)
        self.repos = []
        self.logger.debug(
            f"Repository types to sync: {', '.join(self.Meta.repo_types)}",  # pylint: disable=no-member
            extra={"grouping": "GC Repo Syncs"},
        )
        for repo_type in self.Meta.repo_types:  # pylint: disable=no-member
            self.logger.debug(f"Refreshing repositories of type {repo_type}.", extra={"grouping": "GC Repo Syncs"})
            current_repos = get_refreshed_repos(job_obj=self, repo_type=repo_type, data=self.deserialize_data(kwargs))
            if not repo_type == "jinja_repository":
                for current_repo in current_repos:
                    self.repos.append(current_repo)

    def after_return(self, status, retval, task_id, args, kwargs, einfo):  # pylint: disable=too-many-arguments
        """Commit and Push each repo after job is completed."""
        now = make_aware(datetime.now())
        self.logger.debug(
            f"Finished the {self.Meta.name} job execution.",  # pylint: disable=no-member
            extra={"grouping": "GC After Run"},
        )
        if self.repos:
            for repo in self.repos:
                self.logger.debug(
                    f"Pushing {self.Meta.name} results to repo {repo.base_url}.",  # pylint: disable=no-member
                    extra={"grouping": "GC Repo Commit and Push"},
                )
                repo.commit_with_added(f"{self.Meta.name.upper()} JOB {now}")  # pylint: disable=no-member
                repo.push()
        super().after_return(status, retval, task_id, args, kwargs, einfo=einfo)


class ComplianceJob(GoldenConfigJobMixin, FormEntry):
    """Job to to run the compliance engine."""

    class Meta:
        """Meta object boilerplate for compliance."""

        name = "Perform Configuration Compliance"
        description = "Run configuration compliance on your network infrastructure."
        has_sensitive_variables = False
        repo_types = ["intended_repository", "backup_repository"]

    def run(self, *args, **data):
        """Run config compliance report script."""
        self.logger.debug("Starting config compliance nornir play.")
        config_compliance(self.job_result, self.logger.getEffectiveLevel(), data)

    def after_return(self, *args):
        """Commit and Push each repo after job is completed."""
        self.logger.debug("Compliance job completed, no repositories need to be synced in this task.")


class IntendedJob(GoldenConfigJobMixin, FormEntry):
    """Job to to run generation of intended configurations."""

    class Meta:
        """Meta object boilerplate for intended."""

        name = "Generate Intended Configurations"
        description = "Generate the configuration for your intended state."
        has_sensitive_variables = False
        repo_types = ["jinja_repository", "intended_repository"]

    def run(self, *args, **data):
        """Run config generation script."""
        self.logger.debug("Building device settings mapping and running intended config nornir play.")
        config_intended(self.job_result, self.logger.getEffectiveLevel(), data, self)


class BackupJob(GoldenConfigJobMixin, FormEntry):
    """Job to to run the backup job."""

    class Meta:
        """Meta object boilerplate for backup configurations."""

        name = "Backup Configurations"
        description = "Backup the configurations of your network devices."
        has_sensitive_variables = False
        repo_types = ["backup_repository"]

    def run(self, *args, **data):
        """Run config backup process."""
        self.logger.debug("Starting config backup nornir play.")
        config_backup(self.job_result, self.logger.getEffectiveLevel(), data)


class AllGoldenConfig(GoldenConfigJobMixin):
    """Job to to run all three jobs against a single device."""

    device = ObjectVar(model=Device, required=True)
    debug = BooleanVar(description="Enable for more verbose debug logging")

    class Meta:
        """Meta object boilerplate for all jobs to run against a device."""

        name = "Execute All Golden Configuration Jobs - Single Device"
        description = "Process to run all Golden Configuration jobs configured."
        has_sensitive_variables = False
        repo_types = []

    def run(self, *args, **data):
        """Run all jobs."""
        repo_types = []
        if constant.ENABLE_INTENDED:
            repo_types.extend(["jinja_repository", "intended_repository"])
        if constant.ENABLE_BACKUP:
            repo_types.extend(["backup_repository"])
            repo_types = list(set(repo_types) - set())
        if constant.ENABLE_COMPLIANCE:
            repo_types.extend(["intended_repository", "backup_repository"])

        self.Meta.repo_types = repo_types
        if constant.ENABLE_INTENDED:
            IntendedJob().run.__func__(self, **data)  # pylint: disable=too-many-function-args
        if constant.ENABLE_BACKUP:
            BackupJob().run.__func__(self, **data)  # pylint: disable=too-many-function-args
        if constant.ENABLE_COMPLIANCE:
            ComplianceJob().run.__func__(self, **data)  # pylint: disable=too-many-function-args


class AllDevicesGoldenConfig(GoldenConfigJobMixin, FormEntry):
    """Job to to run all three jobs against multiple devices."""

    class Meta:
        """Meta object boilerplate for all jobs to run against multiple devices."""

        name = "Execute All Golden Configuration Jobs - Multiple Device"
        description = "Process to run all Golden Configuration jobs configured against multiple devices."
        has_sensitive_variables = False
        repo_types = []

    def run(self, *args, **data):
        """Run all jobs."""
        repo_types = []
        if constant.ENABLE_INTENDED:
            repo_types.extend(["jinja_repository", "intended_repository"])
        if constant.ENABLE_BACKUP:
            repo_types.extend(["backup_repository"])
            repo_types = list(set(repo_types) - set())
        if constant.ENABLE_COMPLIANCE:
            repo_types.extend(["intended_repository", "backup_repository"])

        self.Meta.repo_types = repo_types
        if constant.ENABLE_INTENDED:
            IntendedJob().run.__func__(self, **data)  # pylint: disable=too-many-function-args
        if constant.ENABLE_BACKUP:
            BackupJob().run.__func__(self, **data)  # pylint: disable=too-many-function-args
        if constant.ENABLE_COMPLIANCE:
            ComplianceJob().run.__func__(self, **data)  # pylint: disable=too-many-function-args


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
        self._plan_status = None

    @property
    def plan_status(self):
        """The default status for ConfigPlan."""
        if self._plan_status is None:
            self._plan_status = config_plan_default_status()
        return self._plan_status

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
                status=self.plan_status,
                plan_result=self.job_result,
            )
            config_plan.feature.set(features)
            config_plan.validated_save()
            _features = ", ".join([str(feat) for feat in features])
            self.logger.info(
                f"Config plan created for `{device}` with feature `{_features}`.", extra={"object": config_plan}
            )

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
                status=self.plan_status,
                plan_result=self.job_result,
            )
            self.logger.info(f"Config plan created for {device} with manual commands.", extra={"object": config_plan})

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
            self.logger.error(error_msg)
            raise ValueError(error_msg)


class DeployConfigPlans(Job):
    """Job to deploy config plans."""

    config_plan = MultiObjectVar(model=ConfigPlan, required=True)
    debug = BooleanVar(description="Enable for more verbose debug logging")

    class Meta:
        """Meta object boilerplate for config plan deployment."""

        name = "Deploy Config Plans"
        description = "Deploy config plans to devices."
        has_sensitive_variables = False

    def run(self, **data):  # pylint: disable=arguments-differ
        """Run config plan deployment process."""
        self.logger.debug("Starting config plan deployment job.")
        config_deployment(self.job_result, self.logger.getEffectiveLevel(), data)


class DeployConfigPlanJobButtonReceiver(JobButtonReceiver):
    """Job button to deploy a config plan."""

    class Meta:
        """Meta object boilerplate for config plan deployment job button."""

        name = "Deploy Config Plan (Job Button Receiver)"
        has_sensitive_variables = False

    def receive_job_button(self, obj):
        """Run config plan deployment process."""
        self.logger.debug("Starting config plan deployment job.")
        data = {"debug": False, "config_plan": ConfigPlan.objects.filter(id=obj.id)}
        config_deployment(self.job_result, self.logger.getEffectiveLevel(), data)


class SyncGoldenConfigWithDynamicGroups(Job):
    """Job to sync (add/remove) GoldenConfig table based on DynamicGroup members."""

    class Meta:
        """Meta object boilerplate for syncing GoldenConfig table."""

        name = "Sync GoldenConfig Table"
        descritption = "Add or remove GoldenConfig entries based on GoldenConfigSettings DynamicGroup members"
        has_sensitive_variables = False

    def run(self):
        """Run GoldenConfig sync."""
        self.logger.debug("Starting sync of GoldenConfig with DynamicGroup membership.")
        gc_dynamic_group_device_pks = GoldenConfig.get_dynamic_group_device_pks()
        gc_device_pks = GoldenConfig.get_golden_config_device_ids()
        device_pks_to_remove = gc_device_pks.difference(gc_dynamic_group_device_pks)
        device_pks_to_add = gc_dynamic_group_device_pks.difference(gc_device_pks)

        gc_entries_to_remove = GoldenConfig.objects.filter(device__in=device_pks_to_remove)
        for gc_entry_removal in gc_entries_to_remove:
            self.logger.debug(f"Removing GoldenConfig entry for {gc_entry_removal}")

        gc_entries_to_remove.delete()

        devices_to_add_gc_entries = Device.objects.filter(pk__in=device_pks_to_add)
        for device in devices_to_add_gc_entries:
            self.logger.debug(f"Adding GoldenConfig entry for device {device.name}")
            GoldenConfig.objects.create(device=device)


register_jobs(BackupJob)
register_jobs(IntendedJob)
register_jobs(ComplianceJob)
register_jobs(GenerateConfigPlans)
register_jobs(DeployConfigPlans)
register_jobs(DeployConfigPlanJobButtonReceiver)
register_jobs(AllGoldenConfig)
register_jobs(AllDevicesGoldenConfig)
register_jobs(SyncGoldenConfigWithDynamicGroups)
