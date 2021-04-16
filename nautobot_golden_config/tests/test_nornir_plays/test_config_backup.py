"""Unit tests for nautobot_golden_config nornir backup."""

# import unittest
# from nautobot_golden_config.nornir_plays.config_backup import get_substitute_lines


# class ConfigBackupTest(unittest.TestCase):
#     """Test Nornir Backup Task."""

#     def test_get_substitute_lines_single(self):
#         """Validate sub lines works."""
#         sub_lines = get_substitute_lines("<<redacted>>|||fake_regex.+")
#         self.assertEqual(sub_lines, [{"regex_replacement": "<<redacted>>", "regex_search": "fake_regex.+"}])

#     def test_get_substitute_lines_multiple(self):
#         """Validate sub lines works."""
#         sub_lines = get_substitute_lines("<<redacted>>|||fake_regex.+\n<<removed>>|||user.+")
#         self.assertEqual(
#             sub_lines,
#             [
#                 {"regex_replacement": "<<redacted>>", "regex_search": "fake_regex.+"},
#                 {"regex_replacement": "<<removed>>", "regex_search": "user.+"},
#             ],
#         )
