"""Test Utils Functions."""
import unittest
from unittest.mock import patch

from nautobot_golden_config.utilities.utils import get_platform


class GetPlatformTest(unittest.TestCase):
    """Test Get Platform and User Defined Option."""

    def test_get_platform_no_settings_definition(self):
        """Test defaults when settings platform_slug_map not used."""
        assert get_platform("cisco") == "cisco"

    @patch("nautobot_golden_config.utilities.utils.PLUGIN_CFG", {"platform_slug_map": None})
    def test_get_platform_with_key_none(self):
        """Test user defined platform mappings and defaults key defined and set to None."""
        assert get_platform("cisco") == "cisco"

    @patch("nautobot_golden_config.utilities.utils.PLUGIN_CFG", {"platform_slug_map": {"cisco": "cisco_ios"}})
    def test_get_platform_user_defined(self):
        """Test user defined platform mappings."""
        assert get_platform("cisco") == "cisco_ios"
