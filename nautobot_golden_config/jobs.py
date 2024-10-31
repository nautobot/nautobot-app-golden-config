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
from nautobot.extras.models import DynamicGroup, Role, Status, Tag
from nautobot.tenancy.models import Tenant, TenantGroup
from nautobot_plugin_nornir.plugins.inventory.nautobot_orm import NautobotORMInventory
from nornir.core.plugins.inventory import InventoryPluginRegister
from nornir_nautobot.exceptions import NornirNautobotException

from nautobot_golden_config.choices import ConfigPlanTypeChoice
from nautobot_golden_config.exceptions import BackupFailure, ComplianceFailure, IntendedGenerationFailure
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
from nautobot_golden_config.utilities.helper import (
    get_device_to_settings_map,
    get_job_filter,
    update_dynamic_groups_cache,
)

InventoryPluginRegister.register("nautobot-inventory", NautobotORMInventory)

name = "Golden Configuration"  # pylint: disable=invalid-name


def get_repo_types_for_job(job_name):
    """Logic to determine which repo_types are needed based on job + plugin settings."""
    repo_types = []
    if constant.ENABLE_BACKUP and job_name == "nautobot_golden_config.jobs.BackupJob":
        repo_types.extend(["backup_repository"])
    if constant.ENABLE_INTENDED and job_name == "nautobot_golden_config.jobs.IntendedJob":
        repo_types.extend(["jinja_repository", "intended_repository"])
    if constant.ENABLE_COMPLIANCE and job_name == "nautobot_golden_config.jobs.ComplianceJob":
        repo_types.extend(["intended_repository", "backup_repository"])
    if "All" in job_name:
        repo_types.extend(["backup_repository", "jinja_repository", "intended_repository"])
    return repo_types


def get_refreshed_repos(job_obj, repo_types, data=None):
    """Small wrapper to pull latest branch, and return a GitRepo app specific object."""
    dynamic_groups = DynamicGroup.objects.exclude(golden_config_setting__isnull=True)
    repository_records = set()
    for group in dynamic_groups:
        # Make sure the data(device qs) device exist in the dg first.
        if data.filter(group.generate_query()).exists():
            for repo_type in repo_types:
                repo = getattr(group.golden_config_setting, repo_type, None)
                if repo:
                    repository_records.add(repo)

    repositories = {}
    for repository_record in repository_records:
        ensure_git_repository(repository_record, job_obj.logger)
        # TODO: Should this not point to non-nautobot.core import
        # We should ask in nautobot core for the `from_url` constructor to be it's own function
        git_info = get_repo_from_url_to_path_and_from_branch(repository_record)
        git_repo = GitRepo(
            repository_record.filesystem_path,
            git_info.from_url,
            clone_initially=False,
            base_url=repository_record.remote_url,
            nautobot_repo_obj=repository_record,
        )
        commit = False

        if (
            constant.ENABLE_INTENDED
            and "nautobot_golden_config.intendedconfigs" in git_repo.nautobot_repo_obj.provided_contents
        ):
            commit = True
        if (
            constant.ENABLE_BACKUP
            and "nautobot_golden_config.backupconfigs" in git_repo.nautobot_repo_obj.provided_contents
        ):
            commit = True
        repositories[str(git_repo.nautobot_repo_obj.id)] = {"repo_obj": git_repo, "to_commit": commit}
    return repositories


def gc_repo_prep(job, data):
    """Prepare Golden Config git repos for work.

    Args:
        job (Job): Nautobot Job object with logger and other vars.
        data (dict): Data being passed from Job.

    Returns:
        List[GitRepo]: List of GitRepos to be used with Job(s).
    """
    job.logger.debug("Compiling device data for GC job.", extra={"grouping": "Get Job Filter"})
    job.qs = get_job_filter(data)
    job.logger.debug(f"In scope device count for this job: {job.qs.count()}", extra={"grouping": "Get Job Filter"})
    job.logger.debug("Mapping device(s) to GC Settings.", extra={"grouping": "Device to Settings Map"})
    job.device_to_settings_map = get_device_to_settings_map(queryset=job.qs)
    gitrepo_types = list(set(get_repo_types_for_job(job.class_path)))
    job.logger.debug(
        f"Repository types to sync: {', '.join(sorted(gitrepo_types))}",
        extra={"grouping": "GC Repo Syncs"},
    )
    current_repos = get_refreshed_repos(job_obj=job, repo_types=gitrepo_types, data=job.qs)
    return current_repos


def gc_repo_push(job, current_repos, commit_message=""):
    """Push any work from worker to git repos in Job.

    Args:
        job (Job): Nautobot Job with logger and other attributes.
        current_repos (List[GitRepo]): List of GitRepos to be used with Job(s).
    """
    now = make_aware(datetime.now())
    job.logger.debug(
        f"Finished the {job.Meta.name} job execution.",
        extra={"grouping": "GC After Run"},
    )
    if current_repos:
        for _, repo in current_repos.items():
            if repo["to_commit"]:
                job.logger.debug(
                    f"Pushing {job.Meta.name} results to repo {repo['repo_obj'].base_url}.",
                    extra={"grouping": "GC Repo Commit and Push"},
                )
                if not commit_message:
                    commit_message = f"{job.Meta.name.upper()} JOB {now}"
                repo["repo_obj"].commit_with_added(commit_message)
                repo["repo_obj"].push()
                job.logger.info(
                    f'{repo["repo_obj"].nautobot_repo_obj.name}: the new Git repository hash is "{repo["repo_obj"].head}"',
                    extra={
                        "grouping": "GC Repo Commit and Push",
                        "object": repo["repo_obj"].nautobot_repo_obj,
                    },
                )


def gc_repos(func):
    """Decorator used for handle repo syncing, commiting, and pushing."""

    def gc_repo_wrapper(self, *args, **kwargs):
        """Decorator used for handle repo syncing, commiting, and pushing."""
        current_repos = gc_repo_prep(job=self, data=kwargs)
        # This is where the specific jobs run method runs via this decorator.
        try:
            func(self, *args, **kwargs)
        except Exception as error:  # pylint: disable=broad-exception-caught
            error_msg = f"`E3001:` General Exception handler, original error message ```{error}```"
            # Raise error only if the job kwarg (checkbox) is selected to do so on the job execution form.
            if kwargs.get("fail_job_on_task_failure"):
                raise NornirNautobotException(error_msg) from error
        finally:
            gc_repo_push(job=self, current_repos=current_repos, commit_message=kwargs.get("commit_message"))

    return gc_repo_wrapper


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
    """Reused mixin to be able to set defaults for instance attributes in all GC jobs."""

    fail_job_on_task_failure = BooleanVar(description="If any tasks for any device fails, fail the entire job result.")
    commit_message = StringVar(
        label="Git commit message",
        required=False,
        description=r"If empty, defaults to `{job.Meta.name.upper()} JOB {now}`.",
        min_length=2,
        max_length=72,
    )

    def __init__(self, *args, **kwargs):
        """Initialize the job."""
        super().__init__(*args, **kwargs)
        self.qs = None
        self.device_to_settings_map = {}


class ComplianceJob(GoldenConfigJobMixin, FormEntry):
    """Job to to run the compliance engine."""

    class Meta:
        """Meta object boilerplate for compliance."""

        name = "Perform Configuration Compliance"
        description = "Run configuration compliance on your network infrastructure."
        has_sensitive_variables = False

    @gc_repos
    def run(self, *args, **data):  # pylint: disable=unused-argument
        """Run config compliance report script."""
        self.logger.warning("Starting config compliance nornir play.")
        if not constant.ENABLE_COMPLIANCE:
            self.logger.critical("Compliance is disabled in application settings.")
            raise ValueError("Compliance is disabled in application settings.")
        config_compliance(self)


class IntendedJob(GoldenConfigJobMixin, FormEntry):
    """Job to to run generation of intended configurations."""

    class Meta:
        """Meta object boilerplate for intended."""

        name = "Generate Intended Configurations"
        description = "Generate the configuration for your intended state."
        has_sensitive_variables = False

    @gc_repos
    def run(self, *args, **data):  # pylint: disable=unused-argument
        """Run config generation script."""
        self.logger.debug("Building device settings mapping and running intended config nornir play.")
        if not constant.ENABLE_INTENDED:
            self.logger.critical("Intended Generation is disabled in application settings.")
            raise ValueError("Intended Generation is disabled in application settings.")
        config_intended(self)


class BackupJob(GoldenConfigJobMixin, FormEntry):
    """Job to to run the backup job."""

    class Meta:
        """Meta object boilerplate for backup configurations."""

        name = "Backup Configurations"
        description = "Backup the configurations of your network devices."
        has_sensitive_variables = False

    @gc_repos
    def run(self, *args, **data):  # pylint: disable=unused-argument
        """Run config backup process."""
        self.logger.debug("Starting config backup nornir play.")
        if not constant.ENABLE_BACKUP:
            self.logger.critical("Backups are disabled in application settings.")
            raise ValueError("Backups are disabled in application settings.")
        config_backup(self)


class AllGoldenConfig(GoldenConfigJobMixin):
    """Job to to run all three jobs against a single device."""

    device = ObjectVar(model=Device, required=True)
    debug = BooleanVar(description="Enable for more verbose debug logging")

    class Meta:
        """Meta object boilerplate for all jobs to run against a device."""

        name = "Execute All Golden Configuration Jobs - Single Device"
        description = "Process to run all Golden Configuration jobs configured."
        has_sensitive_variables = False

    def run(self, *args, **data):  # pylint: disable=unused-argument, too-many-branches
        """Run all jobs on a single device."""
        current_repos = gc_repo_prep(job=self, data=data)
        failed_jobs = []
        error_msg, jobs_list = "", "All"
        for enabled, play in [
            (constant.ENABLE_INTENDED, config_intended),
            (constant.ENABLE_BACKUP, config_backup),
            (constant.ENABLE_COMPLIANCE, config_compliance),
        ]:
            try:
                if enabled:
                    play(self)
            except BackupFailure:
                self.logger.error("Backup failure occurred!")
                failed_jobs.append("Backup")
            except IntendedGenerationFailure:
                self.logger.error("Intended failure occurred!")
                failed_jobs.append("Intended")
            except ComplianceFailure:
                self.logger.error("Compliance failure occurred!")
                failed_jobs.append("Compliance")
            except Exception as error:  # pylint: disable=broad-exception-caught
                error_msg = f"`E3001:` General Exception handler, original error message ```{error}```"
        gc_repo_push(job=self, current_repos=current_repos, commit_message=data.get("commit_message"))
        if len(failed_jobs) > 1:
            jobs_list = ", ".join(failed_jobs)
        elif len(failed_jobs) == 1:
            jobs_list = failed_jobs[0]
        failure_msg = f"`E3030:` Failure during {jobs_list} Job(s)."
        if len(failed_jobs) > 0:
            self.logger.error(failure_msg)
        if (len(failed_jobs) > 0 or error_msg) and data["fail_job_on_task_failure"]:
            if not error_msg:
                error_msg = failure_msg
            # Raise error only if the job kwarg (checkbox) is selected to do so on the job execution form.
            raise NornirNautobotException(error_msg)


class AllDevicesGoldenConfig(GoldenConfigJobMixin, FormEntry):
    """Job to to run all three jobs against multiple devices."""

    class Meta:
        """Meta object boilerplate for all jobs to run against multiple devices."""

        name = "Execute All Golden Configuration Jobs - Multiple Device"
        description = "Process to run all Golden Configuration jobs configured against multiple devices."
        has_sensitive_variables = False

    def run(self, *args, **data):  # pylint: disable=unused-argument, too-many-branches
        """Run all jobs on multiple devices."""
        current_repos = gc_repo_prep(job=self, data=data)
        failed_jobs = []
        error_msg, jobs_list = "", "All"
        for enabled, play in [
            (constant.ENABLE_INTENDED, config_intended),
            (constant.ENABLE_BACKUP, config_backup),
            (constant.ENABLE_COMPLIANCE, config_compliance),
        ]:
            try:
                if enabled:
                    play(self)
            except BackupFailure:
                self.logger.error("Backup failure occurred!")
                failed_jobs.append("Backup")
            except IntendedGenerationFailure:
                self.logger.error("Intended failure occurred!")
                failed_jobs.append("Intended")
            except ComplianceFailure:
                self.logger.error("Compliance failure occurred!")
                failed_jobs.append("Compliance")
            except Exception as error:  # pylint: disable=broad-exception-caught
                error_msg = f"`E3001:` General Exception handler, original error message ```{error}```"
        gc_repo_push(job=self, current_repos=current_repos, commit_message=data.get("commit_message"))
        if len(failed_jobs) > 1:
            jobs_list = ", ".join(failed_jobs)
        elif len(failed_jobs) == 1:
            jobs_list = failed_jobs[0]
        failure_msg = f"`E3030:` Failure during {jobs_list} Job(s)."
        if len(failed_jobs) > 0:
            self.logger.error(failure_msg)
        if (len(failed_jobs) > 0 or error_msg) and data["fail_job_on_task_failure"]:
            if not error_msg:
                error_msg = failure_msg
            # Raise error only if the job kwarg (checkbox) is selected to do so on the job execution form.
            raise NornirNautobotException(error_msg)


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

            if not all(isinstance(config_set, str) for config_set in config_sets):
                config_set = config_sets
            else:
                config_set = "\n".join(config_sets)
            config_plan = ConfigPlan.objects.create(
                device=device,
                plan_type=self._plan_type,
                config_set=config_set,
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
            "request": self.request,  # pylint: disable=no-member
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
        self.logger.debug("Updating Dynamic Group Cache.")
        update_dynamic_groups_cache()
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

    def __init__(self, *args, **kwargs):
        """Initialize the job."""
        super().__init__(*args, **kwargs)
        self.data = {}

    def run(self, **data):  # pylint: disable=arguments-differ
        """Run config plan deployment process."""
        self.logger.debug("Updating Dynamic Group Cache.")
        update_dynamic_groups_cache()
        self.logger.debug("Starting config plan deployment job.")
        self.data = data
        config_deployment(self)


class DeployConfigPlanJobButtonReceiver(JobButtonReceiver):
    """Job button to deploy a config plan."""

    class Meta:
        """Meta object boilerplate for config plan deployment job button."""

        name = "Deploy Config Plan (Job Button Receiver)"
        has_sensitive_variables = False

    def __init__(self, *args, **kwargs):
        """Initialize the job."""
        super().__init__(*args, **kwargs)
        self.data = {}

    def receive_job_button(self, obj):
        """Run config plan deployment process."""
        self.logger.debug("Updating Dynamic Group Cache.")
        update_dynamic_groups_cache()
        self.logger.debug("Starting config plan deployment job.")
        self.data = {"debug": False, "config_plan": ConfigPlan.objects.filter(id=obj.id)}
        config_deployment(self)


class SyncGoldenConfigWithDynamicGroups(Job):
    """Job to sync (add/remove) GoldenConfig table based on DynamicGroup members."""

    class Meta:
        """Meta object boilerplate for syncing GoldenConfig table."""

        name = "Sync GoldenConfig Table"
        descritption = "Add or remove GoldenConfig entries based on GoldenConfigSettings DynamicGroup members"
        has_sensitive_variables = False

    def run(self):
        """Run GoldenConfig sync."""
        self.logger.debug("Updating Dynamic Group Cache.")
        update_dynamic_groups_cache()
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
