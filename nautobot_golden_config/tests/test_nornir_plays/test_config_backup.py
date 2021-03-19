"""Unit tests for nautobot_golden_config nornir backup.

(c) 2020-2021 Network To Code
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at
  http://www.apache.org/licenses/LICENSE-2.0
Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import unittest
from nautobot_golden_config.nornir_plays.config_backup import get_substitute_lines


class ConfigBackupTest(unittest.TestCase):
    """Test Nornir Backup Task."""

    def test_get_substitute_lines_single(self):
        """Validate sub lines works."""
        sub_lines = get_substitute_lines("<<redacted>>|||fake_regex.+")
        self.assertEqual(sub_lines, [{"regex_replacement": "<<redacted>>", "regex_search": "fake_regex.+"}])

    def test_get_substitute_lines_multiple(self):
        """Validate sub lines works."""
        sub_lines = get_substitute_lines("<<redacted>>|||fake_regex.+\n<<removed>>|||user.+")
        self.assertEqual(sub_lines, [{"regex_replacement": "<<redacted>>", "regex_search": "fake_regex.+"}, {"regex_replacement": "<<removed>>", "regex_search": "user.+"}])
