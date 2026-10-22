"""Unit tests for nautobot_golden_config.utilities.logger."""

import logging
import unittest
from unittest.mock import MagicMock

from nautobot_golden_config.utilities.logger import NornirLogger


class NornirLoggerTestCase(unittest.TestCase):
    """Test NornirLogger only records messages at or above its log level."""

    def test_messages_below_log_level_are_not_recorded(self):
        job_result = MagicMock()
        logger = NornirLogger(job_result, logging.INFO)

        logger.debug("debug message")
        logger.info("info message")

        job_result.log.assert_called_once_with("info message", level_choice="info", obj=None, grouping="")

    def test_debug_messages_recorded_at_debug_level(self):
        job_result = MagicMock()
        logger = NornirLogger(job_result, logging.DEBUG)

        logger.debug("debug message")

        job_result.log.assert_called_once_with("debug message", level_choice="debug", obj=None, grouping="")
