"""Processor used by Golden Config to catch unknown errors."""

from nornir.core.inventory import Host
from nornir.core.task import MultiResult, Result, Task
from nornir_nautobot.exceptions import NornirNautobotException
from nornir_nautobot.plugins.processors import BaseLoggingProcessor


class ProcessGoldenConfig(BaseLoggingProcessor):
    """Processor class for golden configuration jobs."""

    def __init__(self, logger):
        """Set logging facility."""
        self.logger = logger

    def _find_result_exceptions(self, result):
        """Walk the results and return only valid Exceptions.

        NornirNautobotException is expected to be raised in some situations.
        """
        valid_exceptions = []
        if result.failed:
            if isinstance(result, MultiResult) and hasattr(result, "exception"):
                if not isinstance(result.exception, NornirNautobotException):
                    # return exception and traceback output
                    valid_exceptions.append([result.exception, result.result])
            elif isinstance(result, Result) and hasattr(result, "exception"):
                if not isinstance(result.exception, NornirNautobotException):
                    # return exception and traceback output
                    valid_exceptions.append([result.exception, result.result])
            elif hasattr(result, "exception") and hasattr(result.exception, "result"):
                for exception_result in result.exception.result:
                    valid_exceptions += self._find_result_exceptions(exception_result)
        return valid_exceptions

    def task_instance_completed(self, task: Task, host: Host, result: MultiResult) -> None:
        """Nornir processor task completion for golden configurations.

        Args:
            task (Task): Nornir task individual object
            host (Host): Host object with Nornir
            result (MultiResult): Result from Nornir task

        Returns:
            None
        """
        host.close_connections()
        exceptions = self._find_result_exceptions(result)

        if result.failed and exceptions:
            exception_string = ", ".join([str(e[0]) for e in exceptions])
            # Log only exception summary to users
            self.logger.error(f"{task.name} failed: {exception_string}", extra={"object": task.host.data["obj"]})
