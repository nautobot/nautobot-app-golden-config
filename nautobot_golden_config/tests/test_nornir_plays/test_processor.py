"""Tests for the Golden Config Nornir processor."""

from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase
from nornir.core.task import MultiResult, Result

from nautobot_golden_config.nornir_plays.processor import ProcessGoldenConfig


def _multi_result(*results):
    """Build a MultiResult the way the Nornir runner hands one to a processor."""
    multi_result = MultiResult("BACKUP CONFIG")
    multi_result.extend(results)
    return multi_result


def _failed_result():
    """Build a failed Result carrying a live exception, the way `Task.start` does."""
    try:
        raise ValueError("boom")
    except ValueError as error:
        return Result(MagicMock(), exception=error, result="traceback text", failed=True)


def _task_and_host():
    """Throwaway task and host doubles carrying the attributes the processor reads."""
    task = MagicMock()
    task.name = "BACKUP CONFIG"
    task.host.data = {"obj": MagicMock()}
    host = MagicMock()
    host.name = "test_device"
    return task, host


class ProcessGoldenConfigTestCase(SimpleTestCase):
    """Tests for ProcessGoldenConfig.task_instance_completed."""

    def setUp(self):
        """Build a processor with a mock job logger."""
        self.logger = MagicMock()
        self.processor = ProcessGoldenConfig(self.logger)

    @patch("nornir_nautobot.plugins.processors.BaseLoggingProcessor.task_instance_completed")
    def test_base_processor_cleanup_is_invoked(self, mock_base):
        """The base processor releases exception frames and reclaims descriptors.

        Overriding `task_instance_completed` without calling `super()` silently opts out of both,
        which leaks a file descriptor per connection for the lifetime of the play.
        """
        task, host = _task_and_host()
        result = _multi_result(Result(MagicMock(), result="config", failed=False))

        self.processor.task_instance_completed(task, host, result)

        mock_base.assert_called_once_with(task, host, result)

    @patch("nornir_nautobot.plugins.processors.BaseLoggingProcessor.task_instance_completed")
    def test_base_processor_cleanup_is_invoked_on_failure(self, mock_base):
        """Cleanup must run for failed task instances too, which is where frames are pinned."""
        task, host = _task_and_host()
        result = _multi_result(_failed_result())

        self.processor.task_instance_completed(task, host, result)

        mock_base.assert_called_once_with(task, host, result)
        self.logger.error.assert_called_once()

    def test_connections_are_closed(self):
        """Each completed task instance closes the host's connections."""
        task, host = _task_and_host()
        result = _multi_result(Result(MagicMock(), result="config", failed=False))

        self.processor.task_instance_completed(task, host, result)

        host.close_connections.assert_called_once_with()
