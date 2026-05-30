"""Jobs to run backups, intended config, and compliance."""

# pylint: disable=too-many-function-args,logging-fstring-interpolation
# TODO: Remove the following ignore, added to be able to pass pylint in CI.
# pylint: disable=arguments-differ

from datetime import datetime

from django.utils.timezone import make_aware
from nautobot.apps.jobs import (
    BooleanVar,
    ChoiceVar,
    Job,
    JobButtonReceiver,
    MultiObjectVar,
    ObjectVar,
    StringVar,
    TextVar,
    register_jobs,
)
from nautobot.dcim.models import Device, DeviceType, Location, Manufacturer, Platform, Rack, RackGroup
from nautobot.extras.datasources.git import (  # core-import-update
    ensure_git_repository,
    get_repo_from_url_to_path_and_from_branch,
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
    filter_devices_by_feature_enabled,
    format_e3038_message,
    format_e3039_message,
    get_device_to_settings_map,
    get_inscope_settings_from_device_qs,
    get_job_filter,
    update_dynamic_groups_cache,
)

InventoryPluginRegister.register("nautobot-inventory", NautobotORMInventory)

name = "Golden Configuration"  # pylint: disable=invalid-name


def get_refreshed_repos(repository_records):
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


def _filter_config_plans_by_deploy_enabled(logger, config_plan_qs):
    """Drop ConfigPlans whose device's winning GoldenConfigSetting has ``enable_deploy=False``.

    Mirrors the per-device E3038 / E3039 contract used by the other Golden Config jobs: a
    plan whose owning device has the winning Setting's ``enable_deploy`` flag set to ``False``
    is excluded and the device is named in an E3038 entry; when nothing is eligible, a single
    E3039 fires.

    Args:
        logger: Logger that receives warning messages (typically ``self.logger`` on a Job).
        config_plan_qs: QuerySet of ConfigPlan objects to filter. Always non-empty in practice
            — the form's ``MultiObjectVar(required=True)`` and the Job Button path both
            guarantee at least one plan.

    Returns:
        QuerySet[ConfigPlan]: A queryset of plans whose device's winning Setting permits deploy.
    """
    device_qs = Device.objects.filter(config_plan__in=config_plan_qs).distinct()
    enabled_devices = filter_devices_by_feature_enabled(logger, device_qs, "deploy")
    return config_plan_qs.filter(device__in=enabled_devices)


def gc_job_helper(func):
    """Decorator handling GC job setup, repo syncing, and pushing."""

    def gc_job_wrapper(self, *args, **kwargs):
        """Decorator used for GC job setup, repo syncing, commiting, and pushing."""
        self.gc_job_setup(data=kwargs)
        try:
            func(self, *args, **kwargs)
        except Exception as error:  # pylint: disable=broad-exception-caught
            error_msg = f"`E3001:` General Exception handler, original error message ```{error}```"
            if kwargs.get("fail_job_on_task_failure"):
                raise NornirNautobotException(error_msg) from error
        finally:
            gc_repo_push(
                job=self,
                current_repos=get_refreshed_repos(self.repos_to_push),
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
    device_type = MultiObjectVar(model=DeviceType, required=False, display_field="model")
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
        self.device_to_settings = {}
        self.gc_advanced_settings_filter = {}
        self.job_function = ""
        self.repos_to_push = []

    def gc_job_setup(self, data):
        """Handles the setup for the Golden Config job.

        Syncs all in-scope Settings' repositories unconditionally — even when the per-feature
        ``enable_*`` flag is False — per the "Always sync repos if a device is in scope"
        rule in the PR contract. Push targets are still gated by the ``enable_*`` flags
        inside ``get_repos_for_settings``.
        """
        self.job_function = JOB_FUNCTION_MAP[self.name]
        self.qs = get_job_filter(data=data)
        self.device_to_settings = get_device_to_settings_map(self.qs)
        self.gc_advanced_settings_filter = self._build_advanced_settings_filter()
        self._get_repos_to_sync()
        if self.job_function == "all":
            # All-in-one jobs handle per-play filtering and E3038/E3039 in _run_all_plays.
            return
        enabled_qs, disabled_qs = self._get_filtered_queryset(self.job_function)
        self._log_out_of_scope_devices(disabled_qs, self.job_function)
        if enabled_qs.count() == 0:
            self._log_no_eligible_devices(self.job_function, disabled_qs.count(), "job")

    def _build_advanced_settings_filter(self):
        """Pivot the flat ``{device_id: setting}`` map into a per-feature ``True/False`` bucket.

        Returns a ``{feature: {True/False: {device_id: setting}}}`` dict for the features this
        job touches (``backup``/``intended``/``compliance`` for single-feature jobs; all three
        for the all-in-one jobs).
        """
        features = ("backup", "intended", "compliance") if self.job_function == "all" else (self.job_function,)
        result = {feature: {True: {}, False: {}} for feature in features}
        for device_id, setting in self.device_to_settings.items():
            for feature in features:
                is_enabled = bool(getattr(setting, f"enable_{feature}", False))
                result[feature][is_enabled][device_id] = setting
        return result

    def _get_repos_to_sync(self):
        """Sync every in-scope Setting's repos; accumulate push targets gated by enable flags."""
        inscope_gcs = get_inscope_settings_from_device_qs(self.qs)
        if not inscope_gcs:
            return
        repos_to_sync, repos_to_push = GoldenConfigSetting.objects.get_repos_for_settings(
            inscope_gcs, self.job_function
        )
        existing = {repo.pk: repo for repo in self.repos_to_push}
        for repo in repos_to_push:
            existing.setdefault(repo.pk, repo)
        self.repos_to_push = list(existing.values())
        for repository_record in repos_to_sync:
            ensure_git_repository(repository_record, self.logger)

    def _log_no_eligible_devices(self, feature, skipped_count, label):
        """Emit E3039 with appropriate phrasing.

        Args:
            feature: The feature being filtered on. One of ``"backup"``, ``"intended"``,
                ``"compliance"``, ``"plan"``, or ``"deploy"``.
            skipped_count: Number of devices already named by preceding E3038 entries.
            label: ``"job"`` for single-feature jobs (called from ``gc_job_setup``); ``"play"``
                for the per-play emissions inside ``_run_all_plays``.
        """
        msg = format_e3039_message(feature, skipped_count, label)
        if msg is not None:
            self.logger.warning(msg)

    def _log_out_of_scope_devices(self, disabled_devices_qs, feature):
        """Log devices skipped because their highest-weighted setting has the feature disabled.

        See `docs/user/app_use_cases.md` for the rationale behind the highest-weight-wins rule.

        A device only reaches ``disabled_devices_qs`` after being placed in
        ``self.gc_advanced_settings_filter[feature][False]`` by ``_build_advanced_settings_filter``,
        which means it has a winning Setting — so the lookup below cannot return ``None``.
        """
        if not disabled_devices_qs.exists():
            return
        disabled_map = self.gc_advanced_settings_filter[feature][False]
        for device in disabled_devices_qs:
            winning_setting = disabled_map[device.id]
            self.logger.warning(format_e3038_message(device, feature, winning_setting), extra={"object": device})

    def _get_filtered_queryset(self, job_function):
        """Helper for gc_advanced_settings_filter to get filtered queryset."""
        enabled_devs = list(self.gc_advanced_settings_filter[job_function][True].keys())
        disabled_devs = list(self.gc_advanced_settings_filter[job_function][False].keys())
        enabled_qs = self.qs.filter(pk__in=enabled_devs)
        disabled_qs = self.qs.filter(pk__in=disabled_devs)

        # The count summaries are only useful for multi-device jobs. For single-device jobs
        # (``AllGoldenConfig`` always; other jobs when a single device is selected) the same
        # information is conveyed by E3038 (when skipped) or the play actually running
        # (when eligible), so we suppress these to keep the job log focused.
        if self.qs.count() > 1:
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

    def _run_all_plays(self, data):
        """Run intended, backup, and compliance plays for the all-in-one jobs."""
        play_failure_map = {
            BackupFailure: "Backup",
            IntendedGenerationFailure: "Intended",
            ComplianceFailure: "Compliance",
        }
        failed_jobs = []
        for nornir_play in [config_intended, config_backup, config_compliance]:
            play_name = nornir_play.__name__.split("_", 1)[1]
            self.task_qs, disabled_qs = self._get_filtered_queryset(play_name)
            self._log_out_of_scope_devices(disabled_qs, play_name)
            if self.task_qs.count() == 0:
                self._log_no_eligible_devices(play_name, disabled_qs.count(), "play")
                continue
            try:
                nornir_play(self)
            except (BackupFailure, IntendedGenerationFailure, ComplianceFailure) as error:
                label = play_failure_map[type(error)]
                self.logger.error(f"{label} failure occurred!")
                failed_jobs.append(label)
            except Exception as error:  # pylint: disable=broad-exception-caught
                self.logger.error(f"`E3001:` General Exception handler, original error message ```{error}```")
                failed_jobs.append(play_name.capitalize())
        if failed_jobs:
            failure_msg = f"`E3030:` Failure during {', '.join(failed_jobs)} Job(s)."
            self.logger.error(failure_msg)
            if data.get("fail_job_on_task_failure"):
                raise NornirNautobotException(failure_msg)


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
        if self.task_qs.count() == 0:
            return
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
        if self.task_qs.count() == 0:
            return
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
        if self.task_qs.count() == 0:
            return
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

    @gc_job_helper
    def run(self, *args, **data):  # pylint: disable=unused-argument
        """Run all jobs on a single device."""
        self._run_all_plays(data)


class AllDevicesGoldenConfig(GoldenConfigJobMixin, FormEntry):
    """Job to to run all three jobs against multiple devices."""

    class Meta:
        """Meta object boilerplate for all jobs to run against multiple devices."""

        name = "Execute All Golden Configuration Jobs - Multiple Device"
        description = "Process to run all Golden Configuration jobs configured against multiple devices."
        has_sensitive_variables = False

    @gc_job_helper
    def run(self, *args, **data):  # pylint: disable=unused-argument
        """Run all jobs on multiple devices."""
        self._run_all_plays(data)


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
        self._validate_inputs(data)
        try:
            self._device_qs = get_job_filter(data)
        except NornirNautobotException as error:
            error_msg = str(error)
            self.logger.error(error_msg)
            raise NornirNautobotException(error_msg) from error

        # Gate generation on each device's winning GoldenConfigSetting.enable_plan flag —
        # devices whose winning Setting has enable_plan=False are dropped here (E3038 names
        # the Setting and weight; E3039 fires if nothing remains).
        self._device_qs = filter_devices_by_feature_enabled(self.logger, self._device_qs, "plan")
        if not self._device_qs.exists():
            return

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
    fail_job_on_task_failure = BooleanVar(description="If any tasks for any device fails, fail the entire job result.")
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
        self.logger.debug("Starting config plan deployment job.")
        # ``_filter_config_plans_by_deploy_enabled`` refreshes the DynamicGroup cache as a side effect.
        config_plan_qs = _filter_config_plans_by_deploy_enabled(self.logger, data["config_plan"])
        if not config_plan_qs.exists():
            return
        self.data = {**data, "config_plan": config_plan_qs}
        try:
            config_deployment(self)
        except Exception as error:  # pylint: disable=broad-exception-caught
            error_msg = f"`E3001:` General Exception handler, original error message ```{error}```"
            self.logger.error(error_msg)
            if data.get("fail_job_on_task_failure"):
                raise NornirNautobotException(error_msg) from error


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
        self.logger.debug("Starting config plan deployment job.")
        # ``_filter_config_plans_by_deploy_enabled`` refreshes the DynamicGroup cache as a side effect.
        config_plan_qs = _filter_config_plans_by_deploy_enabled(self.logger, ConfigPlan.objects.filter(id=obj.id))
        if not config_plan_qs.exists():
            return
        self.data = {"debug": False, "config_plan": config_plan_qs}
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
