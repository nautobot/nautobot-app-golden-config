"""Customer logger to support writing to console and db."""

import logging
from typing import Any

LOGGER = logging.getLogger("NORNIR_LOGGER")

handler = logging.StreamHandler()
handler.setLevel(logging.NOTSET)
LOGGER.addHandler(handler)
LOGGER_ADAPTER = logging.LoggerAdapter(LOGGER, extra={})


class NornirLogger:
    """Logger that handles same signature as standard Python Library logging but also write to db."""

    def __init__(self, job_result, log_level: int):
        """Initialize the object."""
        self.job_result = job_result
        LOGGER.setLevel(log_level)

    def _logging_helper(self, attr: str, message: str, extra: Any = None):
        """Logger helper to set both db and console logs at once."""
        if not extra:
            extra = {}
        getattr(LOGGER_ADAPTER, attr)(message, extra=extra)
        self.job_result.log(message, level_choice=attr, obj=extra.get("object"), grouping=extra.get("grouping", ""))

    def debug(self, message: str, extra: Any = None):
        """Match standard Python Library debug signature."""
        self._logging_helper("debug", message, extra)

    def info(self, message: str, extra: Any = None):
        """Match standard Python Library info signature."""
        self._logging_helper("info", message, extra)

    def warning(self, message: str, extra: Any = None):
        """Match standard Python Library warning signature."""
        self._logging_helper("warning", message, extra)

    def error(self, message: str, extra: Any = None):
        """Match standard Python Library error signature."""
        self._logging_helper("error", message, extra)

    def critical(self, message: str, extra: Any = None):
        """Match standard Python Library critical signature."""
        self._logging_helper("critical", message, extra)
