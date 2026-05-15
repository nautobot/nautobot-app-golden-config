"""Tests for the Golden Config jobs.

Contract under test (per PR #984):
    - Devices are routed by the highest-weighted ``GoldenConfigSetting`` whose DynamicGroup
      matches them. Ties broken by name.
    - For a feature whose enable flag is ``False`` on the winning Setting, the device is
      skipped and a single ``E3038`` warning is emitted naming the winning Setting and weight.
    - If after filtering the per-job queryset is empty, a single ``E3039`` warning fires.
    - ``ensure_git_repository`` is called for every repo that needs syncing per the
      ``get_repos_for_settings`` contract; ``gc_repo_push`` receives only the repos eligible
      for push (enable-flag-gated, per repo type).
"""

from unittest.mock import MagicMock, patch

from django.contrib.contenttypes.models import ContentType
from nautobot.apps.choices import JobResultStatusChoices
from nautobot.apps.testing import TransactionTestCase, create_job_result_and_run_job
from nautobot.dcim.models import Device
from nautobot.extras.models import DynamicGroup, GitRepository, JobLogEntry

from nautobot_golden_config import jobs
from nautobot_golden_config.models import GoldenConfigSetting
from nautobot_golden_config.tests.conftest import (
    create_device,
    create_orphan_device,
    dgs_gc_settings_and_job_repo_objects,
)


def _sync_targets(mock_ensure):
    """Return the set of GitRepository instances ``ensure_git_repository`` was called with."""
    return {call.args[0] for call in mock_ensure.call_args_list}


def _push_targets(mock_push):
    """Return the set of GitRepository instances passed to ``gc_repo_push``.

    Pairs with the ``get_refreshed_repos`` identity-passthrough patch — ``current_repos``
    is the list of GitRepository instances rather than wrapped ``GitRepo`` objects.
    """
    if not mock_push.called:
        return set()
    return set(mock_push.call_args.kwargs.get("current_repos", []))


def _e30xx(job_result, code):
    """Return JobLogEntry messages whose text starts with the given error code on this JobResult.

    Prefix-match (not substring) so a message that references another code in its body —
    e.g. an E3039 summary that points back to the preceding E3038 entries — isn't double-counted.
    """
    return list(
        JobLogEntry.objects.filter(job_result=job_result, message__startswith=code).values_list("message", flat=True)
    )


def _disable_feature(setting_name, **flags):
    """Toggle one or more ``enable_*`` flags on a Setting by name (saves with ``update``)."""
    GoldenConfigSetting.objects.filter(name=setting_name).update(**flags)


@patch("nautobot_golden_config.nornir_plays.config_backup.run_backup", MagicMock(return_value="foo"))
@patch.object(jobs, "get_refreshed_repos", side_effect=list)
@patch.object(jobs, "gc_repo_push")
@patch.object(jobs, "ensure_git_repository")
class BackupJobContractTestCase(TransactionTestCase):
    """E3038 / E3039 / sync / push contract for ``BackupJob``."""

    databases = ("default", "job_logs")

    def setUp(self):
        self.device = create_device(name="foobaz")
        self.device2 = create_orphan_device(name="foobaz2")
        dgs_gc_settings_and_job_repo_objects()
        self.backup_repo_1 = GitRepository.objects.get(name="test-backup-repo-1")
        self.backup_repo_2 = GitRepository.objects.get(name="test-backup-repo-2")
        super().setUp()

    def test_two_settings_both_enabled(self, mock_ensure, mock_push, *_):
        """Two devices, each in a different Setting; both Settings have backup enabled."""
        job_result = create_job_result_and_run_job(
            module="nautobot_golden_config.jobs",
            name="BackupJob",
            device=Device.objects.all(),
        )

        self.assertEqual(_sync_targets(mock_ensure), {self.backup_repo_1, self.backup_repo_2})
        self.assertEqual(_push_targets(mock_push), {self.backup_repo_1, self.backup_repo_2})
        self.assertEqual(_e30xx(job_result, "E3038"), [])
        self.assertEqual(_e30xx(job_result, "E3039"), [])

    def test_disabled_setting_skips_device_but_still_syncs_repo(self, mock_ensure, mock_push, *_):
        """Setting 2 has backup disabled — device2 is skipped (E3038).

        Both Settings' backup_repos sync per the "Always sync" rule; only Setting 1's
        backup_repo is pushed because Setting 2 has the feature disabled.
        """
        _disable_feature("test_name2", enable_backup=False)

        job_result = create_job_result_and_run_job(
            module="nautobot_golden_config.jobs",
            name="BackupJob",
            device=Device.objects.all(),
        )

        self.assertEqual(_sync_targets(mock_ensure), {self.backup_repo_1, self.backup_repo_2})
        self.assertEqual(_push_targets(mock_push), {self.backup_repo_1})

        e3038s = _e30xx(job_result, "E3038")
        self.assertEqual(len(e3038s), 1)
        self.assertIn(self.device2.name, e3038s[0])
        self.assertIn("test_name2", e3038s[0])
        self.assertIn("weight 1000", e3038s[0])

    def test_all_settings_disabled_still_syncs_emits_e3039_no_push(self, mock_ensure, mock_push, *_):
        """Both Settings disabled — repos still sync (read-side stays fresh); no push; E3039 fires."""
        _disable_feature("test_name", enable_backup=False)
        _disable_feature("test_name2", enable_backup=False)

        job_result = create_job_result_and_run_job(
            module="nautobot_golden_config.jobs",
            name="BackupJob",
            device=Device.objects.all(),
        )

        self.assertEqual(_sync_targets(mock_ensure), {self.backup_repo_1, self.backup_repo_2})
        self.assertEqual(_push_targets(mock_push), set())

        e3038s = _e30xx(job_result, "E3038")
        self.assertEqual(len(e3038s), 2)
        e3039s = _e30xx(job_result, "E3039")
        self.assertEqual(len(e3039s), 1)
        self.assertIn("backup", e3039s[0].lower())
        self.assertIn("2 in-scope devices", e3039s[0])

    @patch.object(jobs, "get_job_filter")
    def test_no_devices_in_scope_emits_bare_e3039_with_no_e3038(self, mock_get_job_filter, *_):
        """``skipped_count == 0``: no device mapped to any Setting — bare E3039, no E3038."""
        mock_get_job_filter.return_value = Device.objects.none()

        job_result = create_job_result_and_run_job(
            module="nautobot_golden_config.jobs",
            name="BackupJob",
            device=Device.objects.all(),
        )

        # Belt-and-suspenders: confirm the job actually ran to completion rather than silently
        # blowing up before reaching the E3039 emission site.
        self.assertEqual(job_result.status, JobResultStatusChoices.STATUS_SUCCESS)

        # No E3038 — nothing was in scope to skip in the first place.
        self.assertEqual(_e30xx(job_result, "E3038"), [])
        e3039s = _e30xx(job_result, "E3039")
        self.assertEqual(len(e3039s), 1)
        self.assertIn("no devices in scope", e3039s[0].lower())


@patch("nautobot_golden_config.nornir_plays.config_intended.run_template", MagicMock(return_value="foo"))
@patch.object(jobs, "get_refreshed_repos", side_effect=list)
@patch.object(jobs, "gc_repo_push")
@patch.object(jobs, "ensure_git_repository")
class IntendedJobContractTestCase(TransactionTestCase):
    """E3038 / E3039 / sync / push contract for ``IntendedJob``.

    Intended syncs both ``intended_repository`` and ``jinja_repository`` but only pushes
    ``intended_repository`` when ``enable_intended=True``.
    """

    databases = ("default", "job_logs")

    def setUp(self):
        self.device = create_device(name="foobaz")
        self.device2 = create_orphan_device(name="foobaz2")
        dgs_gc_settings_and_job_repo_objects()
        self.intended_repo_1 = GitRepository.objects.get(name="test-intended-repo-1")
        self.intended_repo_2 = GitRepository.objects.get(name="test-intended-repo-2")
        self.jinja_repo = GitRepository.objects.get(name="test-jinja-repo-1")
        super().setUp()

    def test_two_settings_both_enabled(self, mock_ensure, mock_push, *_):
        job_result = create_job_result_and_run_job(
            module="nautobot_golden_config.jobs",
            name="IntendedJob",
            device=Device.objects.all(),
        )

        # Both Settings share jinja_repo, so the sync set is {intended_1, intended_2, jinja}.
        self.assertEqual(
            _sync_targets(mock_ensure),
            {self.intended_repo_1, self.intended_repo_2, self.jinja_repo},
        )
        # Push contract: jinja is never pushed; both intended repos are pushed.
        self.assertEqual(_push_targets(mock_push), {self.intended_repo_1, self.intended_repo_2})
        self.assertEqual(_e30xx(job_result, "E3038"), [])
        self.assertEqual(_e30xx(job_result, "E3039"), [])

    def test_disabled_setting_skips_device_but_still_syncs_repos(self, mock_ensure, mock_push, *_):
        """Setting 2 has intended disabled — device2 skipped; all three repos still sync."""
        _disable_feature("test_name2", enable_intended=False)

        job_result = create_job_result_and_run_job(
            module="nautobot_golden_config.jobs",
            name="IntendedJob",
            device=Device.objects.all(),
        )

        # Sync covers both Settings' intended_repos plus the shared jinja_repo.
        self.assertEqual(
            _sync_targets(mock_ensure),
            {self.intended_repo_1, self.intended_repo_2, self.jinja_repo},
        )
        # Only the enabled Setting's intended_repo pushes; jinja never pushes.
        self.assertEqual(_push_targets(mock_push), {self.intended_repo_1})

        e3038s = _e30xx(job_result, "E3038")
        self.assertEqual(len(e3038s), 1)
        self.assertIn(self.device2.name, e3038s[0])
        self.assertIn("enable_intended=False", e3038s[0])

    def test_all_settings_disabled_still_syncs_emits_e3039_no_push(self, mock_ensure, mock_push, *_):
        _disable_feature("test_name", enable_intended=False)
        _disable_feature("test_name2", enable_intended=False)

        job_result = create_job_result_and_run_job(
            module="nautobot_golden_config.jobs",
            name="IntendedJob",
            device=Device.objects.all(),
        )

        # Repos still sync — both intended_repos plus jinja.
        self.assertEqual(
            _sync_targets(mock_ensure),
            {self.intended_repo_1, self.intended_repo_2, self.jinja_repo},
        )
        self.assertEqual(_push_targets(mock_push), set())
        self.assertEqual(len(_e30xx(job_result, "E3038")), 2)
        e3039s = _e30xx(job_result, "E3039")
        self.assertEqual(len(e3039s), 1)
        self.assertIn("intended", e3039s[0].lower())
        self.assertIn("2 in-scope devices", e3039s[0])


@patch("nautobot_golden_config.nornir_plays.config_compliance.run_compliance", MagicMock(return_value="foo"))
@patch.object(jobs, "get_refreshed_repos", side_effect=list)
@patch.object(jobs, "gc_repo_push")
@patch.object(jobs, "ensure_git_repository")
class ComplianceJobContractTestCase(TransactionTestCase):
    """Compliance syncs both backup + intended repos but never pushes."""

    databases = ("default", "job_logs")

    def setUp(self):
        self.device = create_device(name="foobaz")
        self.device2 = create_orphan_device(name="foobaz2")
        dgs_gc_settings_and_job_repo_objects()
        self.backup_repo_1 = GitRepository.objects.get(name="test-backup-repo-1")
        self.backup_repo_2 = GitRepository.objects.get(name="test-backup-repo-2")
        self.intended_repo_1 = GitRepository.objects.get(name="test-intended-repo-1")
        self.intended_repo_2 = GitRepository.objects.get(name="test-intended-repo-2")
        super().setUp()

    def test_two_settings_both_enabled_never_pushes(self, mock_ensure, mock_push, *_):
        job_result = create_job_result_and_run_job(
            module="nautobot_golden_config.jobs",
            name="ComplianceJob",
            device=Device.objects.all(),
        )

        self.assertEqual(
            _sync_targets(mock_ensure),
            {self.backup_repo_1, self.backup_repo_2, self.intended_repo_1, self.intended_repo_2},
        )
        # Compliance never pushes — gc_repo_push is still invoked, but with no repos.
        self.assertEqual(_push_targets(mock_push), set())
        self.assertEqual(_e30xx(job_result, "E3038"), [])

    def test_disabled_compliance_skips_device_but_still_syncs_all_repos(self, mock_ensure, _mock_push, *_):
        """Setting 2 has compliance disabled — device2 is skipped (E3038).

        Compliance reads from both backup_repo and intended_repo so per the "Always sync"
        rule both Settings' repos must still sync (even for the disabled Setting).
        """
        _disable_feature("test_name2", enable_compliance=False)

        job_result = create_job_result_and_run_job(
            module="nautobot_golden_config.jobs",
            name="ComplianceJob",
            device=Device.objects.all(),
        )

        self.assertEqual(
            _sync_targets(mock_ensure),
            {self.backup_repo_1, self.backup_repo_2, self.intended_repo_1, self.intended_repo_2},
        )

        e3038s = _e30xx(job_result, "E3038")
        self.assertEqual(len(e3038s), 1)
        self.assertIn("compliance", e3038s[0])
        self.assertIn(self.device2.name, e3038s[0])


@patch("nautobot_golden_config.nornir_plays.config_backup.run_backup", MagicMock(return_value="foo"))
@patch("nautobot_golden_config.nornir_plays.config_intended.run_template", MagicMock(return_value="foo"))
@patch("nautobot_golden_config.nornir_plays.config_compliance.run_compliance", MagicMock(return_value="foo"))
@patch.object(jobs, "get_refreshed_repos", side_effect=list)
@patch.object(jobs, "gc_repo_push")
@patch.object(jobs, "ensure_git_repository")
class AllGoldenConfigContractTestCase(TransactionTestCase):
    """Single-device "All Jobs": disabled plays emit E3038 naming the device; E3039 is suppressed."""

    databases = ("default", "job_logs")

    def setUp(self):
        self.device = create_device(name="foobaz")
        dgs_gc_settings_and_job_repo_objects()
        super().setUp()

    def test_all_features_enabled_runs_all_plays(self, mock_ensure, mock_push, *_):
        job_result = create_job_result_and_run_job(
            module="nautobot_golden_config.jobs",
            name="AllGoldenConfig",
            device=self.device.id,
        )

        # Sync union of backup_repo_1, intended_repo_1, jinja_repo (device only owned by Setting 1).
        synced = _sync_targets(mock_ensure)
        self.assertIn(GitRepository.objects.get(name="test-backup-repo-1"), synced)
        self.assertIn(GitRepository.objects.get(name="test-intended-repo-1"), synced)
        self.assertIn(GitRepository.objects.get(name="test-jinja-repo-1"), synced)

        # Push backup + intended; jinja never pushed.
        pushed = _push_targets(mock_push)
        self.assertEqual(
            pushed,
            {
                GitRepository.objects.get(name="test-backup-repo-1"),
                GitRepository.objects.get(name="test-intended-repo-1"),
            },
        )
        self.assertEqual(_e30xx(job_result, "E3039"), [])

    def test_backup_disabled_logs_only_e3038_for_single_device(self, _mock_ensure, mock_push, *_):
        """Single-device job: the lone device is named by E3038 — E3039 is suppressed as redundant."""
        _disable_feature("test_name", enable_backup=False)

        job_result = create_job_result_and_run_job(
            module="nautobot_golden_config.jobs",
            name="AllGoldenConfig",
            device=self.device.id,
        )

        # E3038 names the skipped device for the backup play; E3039 stays silent for single-device.
        e3038s = _e30xx(job_result, "E3038")
        self.assertEqual(len(e3038s), 1)
        self.assertIn("backup", e3038s[0])
        self.assertEqual(_e30xx(job_result, "E3039"), [])

        # Push set excludes backup_repo; intended_repo is still pushed.
        pushed = _push_targets(mock_push)
        self.assertNotIn(GitRepository.objects.get(name="test-backup-repo-1"), pushed)
        self.assertIn(GitRepository.objects.get(name="test-intended-repo-1"), pushed)

    def test_all_features_disabled_single_device_emits_three_e3038s_no_e3039(self, _mock_ensure, mock_push, *_):
        """Single-device job with all features off: 3 E3038s (one per play), no E3039s, no push."""
        _disable_feature(
            "test_name",
            enable_backup=False,
            enable_intended=False,
            enable_compliance=False,
        )

        job_result = create_job_result_and_run_job(
            module="nautobot_golden_config.jobs",
            name="AllGoldenConfig",
            device=self.device.id,
        )

        e3038s = _e30xx(job_result, "E3038")
        self.assertEqual(len(e3038s), 3)
        # Each play must have produced its own E3038 — not just three messages that happen
        # to start with the code. Pin each feature name to its own message.
        joined = "\n".join(e3038s)
        for feature in ("backup", "intended", "compliance"):
            self.assertIn(f"skipped for {feature} job", joined)
        self.assertEqual(_e30xx(job_result, "E3039"), [])
        self.assertEqual(_push_targets(mock_push), set())


@patch("nautobot_golden_config.nornir_plays.config_backup.run_backup", MagicMock(return_value="foo"))
@patch("nautobot_golden_config.nornir_plays.config_intended.run_template", MagicMock(return_value="foo"))
@patch("nautobot_golden_config.nornir_plays.config_compliance.run_compliance", MagicMock(return_value="foo"))
@patch.object(jobs, "get_refreshed_repos", side_effect=list)
@patch.object(jobs, "gc_repo_push")
@patch.object(jobs, "ensure_git_repository")
class AllDevicesGoldenConfigContractTestCase(TransactionTestCase):
    """Multi-device "All Jobs" mirrors single-device behavior across both settings."""

    databases = ("default", "job_logs")

    def setUp(self):
        self.device = create_device(name="foobaz")
        self.device2 = create_orphan_device(name="foobaz2")
        dgs_gc_settings_and_job_repo_objects()
        super().setUp()

    def test_two_settings_both_enabled(self, mock_ensure, mock_push, *_):
        create_job_result_and_run_job(
            module="nautobot_golden_config.jobs",
            name="AllDevicesGoldenConfig",
            device=Device.objects.all(),
        )

        synced = _sync_targets(mock_ensure)
        self.assertEqual(
            synced,
            {
                GitRepository.objects.get(name="test-backup-repo-1"),
                GitRepository.objects.get(name="test-backup-repo-2"),
                GitRepository.objects.get(name="test-intended-repo-1"),
                GitRepository.objects.get(name="test-intended-repo-2"),
                GitRepository.objects.get(name="test-jinja-repo-1"),
            },
        )
        pushed = _push_targets(mock_push)
        self.assertEqual(
            pushed,
            {
                GitRepository.objects.get(name="test-backup-repo-1"),
                GitRepository.objects.get(name="test-backup-repo-2"),
                GitRepository.objects.get(name="test-intended-repo-1"),
                GitRepository.objects.get(name="test-intended-repo-2"),
            },
        )

    def test_disabled_features_per_setting(self, _mock_ensure, mock_push, *_):
        """Setting 1 disables backup; Setting 2 disables intended.

        Result: backup_repo_1 is not pushed but backup_repo_2 is; intended_repo_1 is pushed
        but intended_repo_2 is not. Both devices still produce two warnings (one E3038 each per
        play that filters them out).
        """
        _disable_feature("test_name", enable_backup=False)
        _disable_feature("test_name2", enable_intended=False)

        create_job_result_and_run_job(
            module="nautobot_golden_config.jobs",
            name="AllDevicesGoldenConfig",
            device=Device.objects.all(),
        )

        pushed = _push_targets(mock_push)
        self.assertNotIn(GitRepository.objects.get(name="test-backup-repo-1"), pushed)
        self.assertIn(GitRepository.objects.get(name="test-backup-repo-2"), pushed)
        self.assertIn(GitRepository.objects.get(name="test-intended-repo-1"), pushed)
        self.assertNotIn(GitRepository.objects.get(name="test-intended-repo-2"), pushed)


@patch("nautobot_golden_config.nornir_plays.config_backup.run_backup", MagicMock(return_value="foo"))
@patch.object(jobs, "get_refreshed_repos", side_effect=list)
@patch.object(jobs, "gc_repo_push")
@patch.object(jobs, "ensure_git_repository")
class WeightPrecedenceTestCase(TransactionTestCase):
    """Highest-weighted Setting wins, with no per-feature fallback to lower-weighted Settings."""

    databases = ("default", "job_logs")

    def setUp(self):
        self.device = create_device(name="foobaz")
        # Wipe singletons + repos created by the device factory's signals.
        GoldenConfigSetting.objects.all().delete()

        # Build two overlapping DynamicGroups that both contain `self.device`.
        dg_high = DynamicGroup.objects.create(
            name="weight-precedence-high",
            content_type=ContentType.objects.get_for_model(Device),
            filter={"name": [self.device.name]},
        )
        dg_low = DynamicGroup.objects.create(
            name="weight-precedence-low",
            content_type=ContentType.objects.get_for_model(Device),
            filter={"name": [self.device.name]},
        )

        self.backup_repo_high = GitRepository.objects.create(
            name="weight-test-backup-high",
            slug="weight-test-backup-high",
            remote_url="http://example.com/high.git",
            branch="main",
            provided_contents=["nautobot_golden_config.backupconfigs"],
        )
        self.backup_repo_low = GitRepository.objects.create(
            name="weight-test-backup-low",
            slug="weight-test-backup-low",
            remote_url="http://example.com/low.git",
            branch="main",
            provided_contents=["nautobot_golden_config.backupconfigs"],
        )

        # high-weight Setting: backup DISABLED (so device should be skipped despite low-weight enabling backup).
        self.setting_high = GoldenConfigSetting.objects.create(
            name="weight-high",
            slug="weight-high",
            weight=2000,
            dynamic_group=dg_high,
            backup_repository=self.backup_repo_high,
            backup_path_template="{{obj.name}}.cfg",
            enable_backup=False,
            enable_intended=False,
            enable_compliance=False,
        )
        self.setting_low = GoldenConfigSetting.objects.create(
            name="weight-low",
            slug="weight-low",
            weight=500,
            dynamic_group=dg_low,
            backup_repository=self.backup_repo_low,
            backup_path_template="{{obj.name}}.cfg",
            enable_backup=True,
            enable_intended=False,
            enable_compliance=False,
        )
        super().setUp()

    def test_disabled_high_weight_setting_blocks_device_even_when_low_weight_enables(self, mock_ensure, mock_push, *_):
        """The high-weight Setting has backup disabled — device must be skipped (E3038 names it).

        Per the "Always sync" rule, both Settings' backup_repos still sync. Push: high-weight
        is disabled (no push); low-weight is enabled, so its repo lands in the push list — the
        actual push is a no-op since no device wrote to it.
        """
        job_result = create_job_result_and_run_job(
            module="nautobot_golden_config.jobs",
            name="BackupJob",
            device=Device.objects.filter(pk=self.device.pk),
        )

        self.assertEqual(_sync_targets(mock_ensure), {self.backup_repo_high, self.backup_repo_low})
        # Push set follows enable flag, not winner; the low-weight push is a no-op.
        self.assertEqual(_push_targets(mock_push), {self.backup_repo_low})

        e3038s = _e30xx(job_result, "E3038")
        self.assertEqual(len(e3038s), 1)
        # E3038 names the winning (high-weight) Setting, not the low-weight loser.
        self.assertIn("weight-high", e3038s[0])
        self.assertIn("weight 2000", e3038s[0])
        self.assertNotIn("weight-low", e3038s[0])

    def test_enabled_high_weight_setting_owns_device(self, mock_ensure, mock_push, *_):
        """Flip the high-weight Setting to enabled — device routes through it."""
        GoldenConfigSetting.objects.filter(name="weight-high").update(enable_backup=True)

        create_job_result_and_run_job(
            module="nautobot_golden_config.jobs",
            name="BackupJob",
            device=Device.objects.filter(pk=self.device.pk),
        )

        # Both Settings' repos sync (always-sync rule).
        self.assertEqual(_sync_targets(mock_ensure), {self.backup_repo_high, self.backup_repo_low})
        # Both Settings have enable_backup=True so both repos are in the push list. The
        # high-weight Setting owns the device's write; the low-weight push is a no-op.
        self.assertEqual(_push_targets(mock_push), {self.backup_repo_high, self.backup_repo_low})
