"""Test cases for Jinja2 filters."""
from unittest import mock

from django.test import SimpleTestCase

from nautobot_golden_config import jinja_filters


@mock.patch.object(jinja_filters, "library")
class TestJinjaFilters(SimpleTestCase):
    """Test cases for Jinja2 filters."""

    @mock.patch("os.path.isdir")
    @mock.patch("os.listdir")
    def test_find_available_files_ignores_invalid_paths(
        self, mock_listdir, mock_isdir, mock_library
    ):  # pylint: disable=unused-argument
        """Test filter."""
        mock_isdir.side_effect = [False, True]
        mock_listdir.side_effect = [["100_aaa.j2", "110_acl.j2"]]
        paths = ["templates/ios", "templates"]
        words = ["aaa"]
        ext = "j2"
        available_files = jinja_filters.find_available_files(paths, words, ext)
        self.assertEqual(available_files, ["100_aaa.j2"])
        mock_isdir.assert_has_calls([mock.call("templates/ios"), mock.call("templates")])
        mock_listdir.assert_called_once()
        mock_listdir.assert_has_calls([mock.call("templates")])

    @mock.patch("os.path.isdir")
    @mock.patch("os.listdir")
    def test_find_available_files_ignores_duplicate_filenames(
        self, mock_listdir, mock_isdir, mock_library
    ):  # pylint: disable=unused-argument
        """Test filter."""
        mock_isdir.side_effect = [True, True]
        mock_listdir.side_effect = [["100_aaa.j2", "110_acl.j2"], ["100_aaa.j2"]]
        paths = ["templates/ios", "templates"]
        words = ["aaa"]
        ext = "j2"
        available_files = jinja_filters.find_available_files(paths, words, ext)
        self.assertEqual(available_files, ["100_aaa.j2"])
        mock_isdir.assert_has_calls([mock.call("templates/ios"), mock.call("templates")])
        mock_listdir.assert_has_calls([mock.call("templates/ios"), mock.call("templates")])

    @mock.patch("os.path.isdir")
    @mock.patch("os.listdir")
    def test_find_available_files_include_files_from_all_directories(
        self, mock_listdir, mock_isdir, mock_library
    ):  # pylint: disable=unused-argument
        """Test filter."""
        mock_isdir.side_effect = [True, True, True]
        mock_listdir.side_effect = [["100_aaa.j2", "110_acl.j2"], ["120_bgp.j2"], ["130_dns.j2"]]
        paths = ["templates/ios/c9300", "templates/ios/backbone", "templates/ios"]
        words = ["aaa", "bgp", "dns"]
        ext = "j2"
        available_files = jinja_filters.find_available_files(paths, words, ext)
        self.assertEqual(set(available_files), set(["100_aaa.j2", "120_bgp.j2", "130_dns.j2"]))

    @mock.patch("os.path.isdir")
    @mock.patch("os.listdir")
    def test_find_available_files_include_files_with_similar_names(
        self, mock_listdir, mock_isdir, mock_library
    ):  # pylint: disable=unused-argument
        """Test filter."""
        mock_isdir.side_effect = [True]
        mock_listdir.side_effect = [["100_aaa.j2", "110_aaa.j2", "120_aaa_not_matching.j2", "130_matching_aaa.j2"]]
        paths = ["templates/ios"]
        words = ["aaa"]
        ext = "j2"
        available_files = jinja_filters.find_available_files(paths, words, ext)
        self.assertEqual(set(available_files), set(["100_aaa.j2", "110_aaa.j2", "130_matching_aaa.j2"]))

    @mock.patch.object(jinja_filters, "collect_preferred_file")
    def test_collect_preferred_files(
        self, mock_collect_preferred_file, mock_library
    ):  # pylint: disable=unused-argument
        paths = ["templates/ios/c9300", "templates/ios"]
        filenames = ["100_aaa.j2", "110_acl.j2"]
        expected = ["templates/ios/100_aaa.j2", "templates/ios/c9300/110_acl.j2"]
        mock_collect_preferred_file.side_effect = expected
        preferred_files = jinja_filters.collect_preferred_files(paths, filenames)
        self.assertEqual(preferred_files, expected)
        mock_collect_preferred_file.assert_has_calls([mock.call(paths, "100_aaa.j2"), mock.call(paths, "110_acl.j2")])

    @mock.patch("os.path.isfile")
    @mock.patch("os.path.abspath")
    def test_collect_preferred_file_first_path_used(
        self, mock_abspath, mock_isfile, mock_library
    ):  # pylint: disable=unused-argument
        mock_abspath.return_value = "/abs/path/to/templates/ios/c9300"
        mock_isfile.return_value = True
        preferred_file = jinja_filters.collect_preferred_file(["templates/ios/c9300", "templates/ios"], "100_aaa.j2")
        expected = "/abs/path/to/templates/ios/c9300/100_aaa.j2"
        self.assertEqual(preferred_file, expected)
        mock_abspath.assert_called_once()
        mock_abspath.assert_has_calls([mock.call("templates/ios/c9300")])
        mock_isfile.assert_called_once()

    @mock.patch("os.path.isfile")
    @mock.patch("os.path.abspath")
    def test_collect_preferred_file_second_path_used(
        self, mock_abspath, mock_isfile, mock_library
    ):  # pylint: disable=unused-argument
        mock_abspath.side_effect = ["/abs/path/to/templates/ios/c9300", "/abs/path/to/templates/ios"]
        mock_isfile.side_effect = [False, True]
        preferred_file = jinja_filters.collect_preferred_file(["templates/ios/c9300", "templates/ios"], "100_aaa.j2")
        expected = "/abs/path/to/templates/ios/100_aaa.j2"
        self.assertEqual(preferred_file, expected)
        mock_abspath.assert_has_calls([mock.call("templates/ios/c9300"), mock.call("templates/ios")])
        mock_isfile.assert_has_calls(
            [
                mock.call("/abs/path/to/templates/ios/c9300/100_aaa.j2"),
                mock.call("/abs/path/to/templates/ios/100_aaa.j2"),
            ]
        )

    @mock.patch("os.path.isfile")
    @mock.patch("os.path.abspath")
    def test_collect_preferred_file_exception_file_not_found(
        self, mock_abspath, mock_isfile, mock_library
    ):  # pylint: disable=unused-argument
        mock_abspath.side_effect = ["/abs/path/to/templates/ios/c9300", "/abs/path/to/templates/ios"]
        mock_isfile.side_effect = [False, False]
        with self.assertRaises(FileNotFoundError):
            jinja_filters.collect_preferred_file(["templates/ios/c9300", "templates/ios"], "100_aaa.j2")

        mock_abspath.assert_has_calls([mock.call("templates/ios/c9300"), mock.call("templates/ios")])
        mock_isfile.assert_has_calls(
            [
                mock.call("/abs/path/to/templates/ios/c9300/100_aaa.j2"),
                mock.call("/abs/path/to/templates/ios/100_aaa.j2"),
            ]
        )
