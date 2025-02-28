"""Basic tests that do not require Django."""

import os
import re
import unittest

import toml
import yaml

from nautobot_golden_config import __version__ as project_version


class TestDocsPackaging(unittest.TestCase):
    """Test Version in doc requirements is the same pyproject."""

    def test_version(self):
        """Verify that pyproject.toml dev dependencies have the same versions as in the docs requirements.txt."""
        parent_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
        poetry_path = os.path.join(parent_path, "pyproject.toml")
        poetry_details = toml.load(poetry_path)["tool"]["poetry"]["group"]["dev"]["dependencies"]
        with open(f"{parent_path}/docs/requirements.txt", "r", encoding="utf-8") as file:
            requirements = [line for line in file.read().splitlines() if (len(line) > 0 and not line.startswith("#"))]
        for pkg in requirements:
            package_name = pkg
            if len(pkg.split("==")) == 2:  # noqa: PLR2004
                package_name, version = pkg.split("==")
            else:
                version = "*"
            self.assertEqual(poetry_details[package_name], version)


class TestDocsReleaseNotes(unittest.TestCase):
    """Test that mkdocs has all of the release notes files that have been created."""

    def __init__(self, *args, **kwargs):
        """Set the parent path and release_notes_files attributes."""
        super().__init__(*args, **kwargs)
        self.parent_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
        docs_path = os.path.join(self.parent_path, "docs")
        self.release_notes_files = [
            file for file in os.listdir(f"{docs_path}/admin/release_notes/") if file.endswith(".md")
        ]

    def test_version_file_found(self):
        """Verify that if the current version has no letters, which would see in alpha or beta has an associated release note file."""
        version_pattern = re.compile(r"^(\d+)\.(\d+)\.\d+$")
        match = version_pattern.match(project_version)
        # If there is no match, then it is likely an alpha or beta version and we can skip this test.
        if match:
            major, minor = match.groups()
            version_str = f"version_{major}.{minor}.md"
            if version_str not in self.release_notes_files:
                self.fail(f"Release note file for version {version_str} not found in release notes folder.")

    def test_mkdocs_files(self):
        """Verify that in the mkdocs key `nav.[Administrator Guide][Release Notes]` has every file accounted for."""

        def _find_release_notes(data):
            """Find the release notes in the mkdocs.yml file as everything is a list with key names and not deterministic."""
            found_docs = []
            for item in data["nav"]:
                if "Administrator Guide" not in item:
                    continue
                for sub_item in item["Administrator Guide"]:
                    if "Release Notes" not in sub_item:
                        continue
                    for release_note in sub_item["Release Notes"]:
                        value = list(release_note.values())[0] if isinstance(release_note, dict) else release_note
                        value = value.split("/")[-1]
                        found_docs.append(value)
                    return found_docs
            return None

        with open(f"{self.parent_path}/mkdocs.yml", "r", encoding="utf-8") as file:
            data = yaml.safe_load(file)
            # We will read the yaml file and get the list of files in the release notes section
            release_notes_mkdocs = _find_release_notes(data)
            if not release_notes_mkdocs:
                self.fail("No release notes found in mkdocs.yml")
            self.assertEqual(set(release_notes_mkdocs), set(self.release_notes_files))
