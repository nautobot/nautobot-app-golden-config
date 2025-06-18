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
from nautobot.extras.models import Role, Status, Tag
from nautobot.tenancy.models import Tenant, TenantGroup
from nautobot_plugin_nornir.plugins.inventory.nautobot_orm import NautobotORMInventory
from nornir.core.plugins.inventory import InventoryPluginRegister
from nornir_nautobot.exceptions import NornirNautobotException

from nautobot_golden_config.choices import ConfigPlanTypeChoice
from nautobot_golden_config.exceptions import BackupFailure, ComplianceFailure, IntendedGenerationFailure
from nautobot_golden_config.models import ComplianceFeature, ConfigPlan, GoldenConfig, GoldenConfigSetting
from nautobot_golden_config.nornir_plays.config_backup import config_backup
from nautobot_golden_config.nornir_plays.config_compliance import config_compliance
from nautobot_golden_config.nornir_plays.config_deployment import config_deployment
from nautobot_golden_config.nornir_plays.config_intended import config_intended
from nautobot_golden_config.utilities.config_plan import (
    config_plan_default_status,
    generate_config_set_from_compliance_feature,
    generate_config_set_from_manual,
)
from nautobot_golden_config.utilities.constant import JOB_FUNCTION_MAP
from nautobot_golden_config.utilities.git import GitRepo
from nautobot_golden_config.utilities.helper import (
    get_device_to_settings_map,
    get_golden_config_settings,
    get_inscope_settings_from_device_qs,
    get_job_filter,
    update_dynamic_groups_cache,
    verify_config_plan_eligibility,
    verify_deployment_eligibility,
)

InventoryPluginRegister.register("nautobot-inventory", NautobotORMInventory)

name = "Golden Configuration"  # pylint: disable=invalid-name


"""
What do we need for each job related to repositories?
- The best GoldenConfigSettings across all inscope devices. should be get_inscope_settings_from_device_qs from helpers.
- Helps with quickly determining if a repo is needed for a job.
- get_repo_types_for_job accompanied by inscope settings gets actual repos.
- Device to settings map. This is a dict of device pk to the GoldenConfigSettings object.

From a device qs, we need to get the following:
- The best GoldenConfigSettings across all inscope devices. should be get_inscope_settings_from_device_qs from helpers.
- Device to settings map. This is a dict of device pk to the GoldenConfigSettings object.
- Repos per inscope settings, if that specific setting is enabled based on the repos needed for the job (get_repo_types_for_job).


Other considerations for (only for compliance job, and all jobs)
- If a setting is disabled, but a repo/repo path is set that means we need to do:
    - Still run ensure_git_repository on the repo.
    - Don't add repo to the list of repos to commit/push.
-----------
Backup job:
- Repo types needed: backup_repository
- Always sync repos if a device is in scope for the job that matches a GC setting.
- If setting is enabled, and repo is set, and if a device is in scope for the job, then we need to commit/push only backup_repository.
- We should log if a device is in the queryset, but the setting is disabled.

Intended job:
- Repo types needed: jinja_repository, intended_repository
- Always sync repos if a device is in scope for the job that matches a GC setting.
- If setting is enabled, and repo is set, and if a device is in scope for the job, then we need to commit/push only intended_repository.
- We should log if a device is in the queryset, but the setting is disabled.
    - Also if templates git repo is not set, but intended is set, and setting is enabled.


Compliance job:
- Repo types needed: intended_repository, backup_repository
- All job:
- Repo types needed: backup_repository, jinja_repository, intended_repository
"""


def get_repo_types_for_job(job_name):
    """Logic to determine which repo_types are needed based on job + plugin settings."""
    repo_types = []
    if job_name == "backup":
        repo_types.append("backup_repository")
    if job_name == "intended":
        repo_types.extend(["jinja_repository", "intended_repository"])
    if job_name == "compliance":
        repo_types.extend(["intended_repository", "backup_repository"])
    if "all" in job_name.lower():
        repo_types.extend(["backup_repository", "jinja_repository", "intended_repository"])
    return repo_types


# def get_refreshed_repos(job_obj, repository_records, gc_setting):
#     """Small wrapper to pull latest branch, and return a GitRepo app specific object."""
#     repositories = {}
#     for repository_record in repository_records:
#         ensure_git_repository(repository_record, job_obj.logger)
#         # TODO: Should this not point to non-nautobot.core import
#         # We should ask in nautobot core for the `from_url` constructor to be it's own function
#         git_info = get_repo_from_url_to_path_and_from_branch(repository_record)
#         git_repo = GitRepo(
#             repository_record.filesystem_path,
#             git_info.from_url,
#             clone_initially=False,
#             base_url=repository_record.remote_url,
#             nautobot_repo_obj=repository_record,
#         )
#         commit = False

#         if (
#             gc_setting.intended_enabled
#             and "nautobot_golden_config.intendedconfigs" in git_repo.nautobot_repo_obj.provided_contents
#         ):
#             commit = True
#         if (
#             gc_setting.backup_enabled
#             and "nautobot_golden_config.backupconfigs" in git_repo.nautobot_repo_obj.provided_contents
#         ):
#             commit = True

#         repositories[str(git_repo.nautobot_repo_obj.id)] = {"repo_obj": git_repo, "to_commit": commit}
#     return repositories


def get_refreshed_reposv2(repository_records):
    """Small wrapper to pull latest branch, and return a list of GitRepo app specific objects."""
    gitrepo_obj = []
    for repository_record in repository_records:
        git_info = get_repo_from_url_to_path_and_from_branch(repository_record)
        git_repo = GitRepo(
            repository_record.filesystem_path,
            git_info.from_url,
            clone_initially=False,
            base_url=repository_record.remote_url,
            nautobot_repo_obj=repository_record,
        )
        gitrepo_obj.append(git_repo)
    return gitrepo_obj


# def gc_repo_prep(job, inscope_gc_settings):
#     """Prepare Golden Config git repos for work.

#     Args:
#         job (Job): Nautobot Job object with logger and other vars.
#         data (dict): Data being passed from Job.

#     Returns:
#         List[GitRepo]: List of GitRepos to be used with Job(s).
#     """
#     gitrepo_types = list(set(get_repo_types_for_job(job.class_path)))
#     if inscope_gc_settings:
#         for gcs in inscope_gc_settings:
#             repos = GoldenConfigSetting.objects.get_repos_for_setting(setting=gcs, repo_types=gitrepo_types)
#             job.logger.debug(
#                 f"Repositories to sync for GC Setting {gcs.name}: {', '.join(sorted([repo.name for repo in repos]))}",
#                 extra={"grouping": "GC Repo Syncs"},
#             )
#             current_repos = get_refreshed_repos(job_obj=job, repository_records=repos, gc_setting=gcs)
#         return current_repos
#     return []


# def gc_repo_push(job, current_repos, commit_message=""):
#     """Push any work from worker to git repos in Job.

#     Args:
#         job (Job): Nautobot Job with logger and other attributes.
#         current_repos (List[GitRepo]): List of GitRepos to be used with Job(s).
#     """
#     now = make_aware(datetime.now())
#     job.logger.debug(
#         f"Finished the {job.Meta.name} job execution.",
#         extra={"grouping": "GC After Run"},
#     )
#     if current_repos:
#         for _, repo in current_repos.items():
#             if repo["to_commit"]:
#                 job.logger.debug(
#                     f"Pushing {job.Meta.name} results to repo {repo['repo_obj'].base_url}.",
#                     extra={"grouping": "GC Repo Commit and Push"},
#                 )
#                 if not commit_message:
#                     commit_message = f"{job.Meta.name.upper()} JOB {now}"
#                 repo["repo_obj"].commit_with_added(commit_message)
#                 repo["repo_obj"].push()
#                 job.logger.info(
#                     f'{repo["repo_obj"].nautobot_repo_obj.name}: the new Git repository hash is "{repo["repo_obj"].head}"',
#                     extra={
#                         "grouping": "GC Repo Commit and Push",
#                         "object": repo["repo_obj"].nautobot_repo_obj,
#                     },
#                 )


def gc_repo_pushv2(job, current_repos, commit_message=""):
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
        for repo in current_repos:
            job.logger.debug(
                f"Pushing {job.Meta.name} results to repo {repo.base_url}.",
                extra={"grouping": "GC Repo Commit and Push"},
            )
            if not commit_message:
                commit_message = f"{job.Meta.name.upper()} JOB {now}"
            repo.commit_with_added(commit_message)
            repo.push()
            job.logger.info(
                f'{repo.nautobot_repo_obj.name}: the new Git repository hash is "{repo.head}"',
                extra={
                    "grouping": "GC Repo Commit and Push",
                    "object": repo.nautobot_repo_obj,
                },
            )


# def gc_repos(func):
#     """Decorator used for handle repo syncing, commiting, and pushing."""

#     def gc_repo_wrapper(self, *args, **kwargs):
#         """Decorator used for handle repo syncing, commiting, and pushing."""
#         self.qs = get_job_filter(data=kwargs)
#         # self.gc_advanced_filter = GCSettingsDeviceFilterSet(self.qs)
#         self.gc_advanced_filter = get_device_to_settings_map(self.qs, self.name)
#         active_settings = set(list(self.gc_advanced_filter[JOB_FUNCTION_MAP[self.name]][True].values()))
#         current_repos = gc_repo_prep(job=self, inscope_gc_settings=active_settings)
#         # This is where the specific jobs run method runs via this decorator.
#         try:
#             func(self, *args, **kwargs)
#         except Exception as error:  # pylint: disable=broad-exception-caught
#             error_msg = f"`E3001:` General Exception handler, original error message ```{error}```"
#             # Raise error only if the job kwarg (checkbox) is selected to do so on the job execution form.
#             if kwargs.get("fail_job_on_task_failure"):
#                 raise NornirNautobotException(error_msg) from error
#         finally:
#             gc_repo_push(job=self, current_repos=current_repos, commit_message=kwargs.get("commit_message", ""))

#     return gc_repo_wrapper


def gc_job_helper(func):
    """Decorator used for handle repo syncing, commiting, and pushing."""

    def gc_job_wrapper(self, *args, **kwargs):
        """Decorator used for GC job setup, repo syncing, commiting, and pushing."""
        self.gc_job_setup(data=kwargs, all_job=False)
        # This is where the specific jobs run method runs via this decorator.
        try:
            func(self, *args, **kwargs)
        except Exception as error:  # pylint: disable=broad-exception-caught
            error_msg = f"`E3001:` General Exception handler, original error message ```{error}```"
            # Raise error only if the job kwarg (checkbox) is selected to do so on the job execution form.
            if kwargs.get("fail_job_on_task_failure"):
                raise NornirNautobotException(error_msg) from error
        finally:
            gc_repo_pushv2(
                job=self,
                current_repos=get_refreshed_reposv2(self.repos_to_push),
                commit_message=kwargs.get("commit_message", ""),
            )

    return gc_job_wrapper


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
        self.qs = Device.objects.none()
        self.task_qs = Device.objects.none()
        self.gc_advanced_settings_filter = {}
        self.job_function = ""
        self.repos_to_push = []

    def gc_job_setup(self, data):
        """Handles the setup for the Golden Config job."""
        self.job_function = JOB_FUNCTION_MAP[self.name]
        self.qs = get_job_filter(data=data)
        self.gc_advanced_settings_filter = get_device_to_settings_map(self.qs, self.job_function)
        if self.job_function.lower() == "all":
            # If the job is "all", we need to set the job_function to each individual job.
            # If the job is one of the all jobs, we need to loop through each job and run the setup for each.
            return
        enabled_qs, disabled_qs = self._get_filtered_queryset(self.job_function)
        self._log_out_of_scope_devices(disabled_qs)
        inscope_gcs = get_inscope_settings_from_device_qs(enabled_qs)
        repos_to_sync, self.repos_to_push = GoldenConfigSetting.objects.get_repos_for_settings(
            inscope_gcs, get_repo_types_for_job(self.job_function)
        )
        if repos_to_sync:
            for repository_record in repos_to_sync:
                ensure_git_repository(repository_record, self.logger)

    def _log_out_of_scope_devices(self, disabled_devices_qs):
        """Log devices that are out of scope for the job."""
        if disabled_devices_qs.count() > 0:
            for device in disabled_devices_qs:
                self.logger.warning(
                    f"E30XX: Device {device.name} does not have the required settings to run the job. Skipping device.",
                    extra={"object": device},
                )

    def _get_filtered_queryset(self, job_function):
        """Helper for gc_advanced_settings_filter to get filtered queryset."""
        enabled_devs = list(self.gc_advanced_settings_filter[job_function][True].keys())
        disabled_devs = list(self.gc_advanced_settings_filter[job_function][False].keys())
        enabled_qs = self.qs.filter(pk__in=enabled_devs)
        disabled_qs = self.qs.filter(pk__in=disabled_devs)

        self.logger.debug(
            f"Device(s) with settings enabled for {job_function} job: {enabled_qs.count()}",
            extra={"grouping": "Get Filtered Queryset"},
        )
        self.logger.debug(
            f"Device(s) with settings disabled for {job_function} job: {disabled_qs.count()}",
            extra={"grouping": "Get Filtered Queryset"},
        )
        self.task_qs = enabled_qs
        return enabled_qs, disabled_qs


class ComplianceJob(GoldenConfigJobMixin, FormEntry):
    """Job to run the compliance engine."""

    class Meta:
        """Meta object boilerplate for compliance."""

        name = "Perform Configuration Compliance"
        description = "Run configuration compliance on your network infrastructure."
        has_sensitive_variables = False

    @gc_job_helper
    def run(self, *args, **data):  # pylint: disable=unused-argument
        """Run config compliance report script."""
        try:
            self.logger.debug("Starting config compliance nornir play.")
            config_compliance(self)
        except NornirNautobotException as error:
            error_msg = str(error)
            self.logger.error(error_msg)
            raise NornirNautobotException(error_msg) from error


class IntendedJob(GoldenConfigJobMixin, FormEntry):
    """Job to to run generation of intended configurations."""

    class Meta:
        """Meta object boilerplate for intended."""

        name = "Generate Intended Configurations"
        description = "Generate the configuration for your intended state."
        has_sensitive_variables = False

    @gc_job_helper
    def run(self, *args, **data):  # pylint: disable=unused-argument
        """Run config generation script."""
        try:
            self.logger.debug("Building device settings mapping and running intended config nornir play.")
            config_intended(self)
        except NornirNautobotException as error:
            error_msg = str(error)
            self.logger.error(error_msg)
            raise NornirNautobotException(error_msg) from error


class BackupJob(GoldenConfigJobMixin, FormEntry):
    """Job to to run the backup job."""

    class Meta:
        """Meta object boilerplate for backup configurations."""

        name = "Backup Configurations"
        description = "Backup the configurations of your network devices."
        has_sensitive_variables = False

    @gc_job_helper
    def run(self, *args, **data):  # pylint: disable=unused-argument
        """Run config backup process."""
        try:
            self.logger.debug("Starting config backup nornir play.")
            config_backup(self)
        except NornirNautobotException as error:
            error_msg = str(error)
            self.logger.error(error_msg)
            raise NornirNautobotException(error_msg) from error


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
        failed_jobs = []
        error_msg, jobs_list = "", "All"
        self.gc_job_setup(data)
        gc_setting = GoldenConfigSetting.objects.get_for_device(data["device"])
        repos_to_sync, self.repos_to_push = GoldenConfigSetting.objects.get_repos_for_settings(
            gc_setting,
            get_repo_types_for_job(self.job_function),
        )
        if repos_to_sync:
            for repository_record in repos_to_sync:
                ensure_git_repository(repository_record, self.logger)
        for nornir_play in [config_intended, config_backup, config_compliance]:
            self.task_qs, _ = self._get_filtered_queryset(nornir_play.__name__.split("_")[1])
            try:
                nornir_play(self)
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
        gc_repo_pushv2(
            job=self,
            current_repos=get_refreshed_reposv2(self.repos_to_push),
            commit_message=data.get("commit_message", ""),
        )
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
        self.gc_job_setup(data)
        failed_jobs = []
        error_msg, jobs_list = "", "All"
        inscope_gcs = get_inscope_settings_from_device_qs(self.qs)
        repos_to_sync, self.repos_to_push = GoldenConfigSetting.objects.get_repos_for_settings(
            inscope_gcs,
            get_repo_types_for_job(self.job_function),
        )
        if repos_to_sync:
            for repository_record in repos_to_sync:
                ensure_git_repository(repository_record, self.logger)
        for nornir_play in [config_intended, config_backup, config_compliance]:
            self.task_qs, _ = self._get_filtered_queryset(nornir_play.__name__.split("_")[1])
            try:
                nornir_play(self)
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
        gc_repo_pushv2(
            job=self,
            current_repos=get_refreshed_reposv2(self.repos_to_push),
            commit_message=data.get("commit_message", ""),
        )
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
        self.logger.debug("Starting config plan generation job.")
        settings = get_golden_config_settings()

        self._validate_inputs(data)
        try:
            self._device_qs = get_job_filter(data)

            # Verify plan eligibility for each device
            for device in self._device_qs:
                verify_config_plan_eligibility(self.logger, device, settings)

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
        settings = get_golden_config_settings()

        # Verify deployment eligibility for each config plan
        for config_plan in self.data["config_plan"]:
            verify_deployment_eligibility(self.logger, config_plan, settings)

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
