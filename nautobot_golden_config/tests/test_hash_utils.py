"""Unit tests for nautobot_golden_config.utilities.hash_utils."""

import hashlib
import json

from nautobot.apps.testing import TestCase

from nautobot_golden_config.utilities.hash_utils import compute_config_hash, normalize_config_content

EMPTY_SHA256 = hashlib.sha256(b"").hexdigest()


class NormalizeConfigContentTestCase(TestCase):
    """Cover every branch of ``normalize_config_content``."""

    def test_empty_string_returns_empty(self):
        self.assertEqual(normalize_config_content(""), "")

    def test_none_returns_empty(self):
        self.assertEqual(normalize_config_content(None), "")

    def test_empty_dict_returns_empty(self):
        self.assertEqual(normalize_config_content({}), "")

    def test_empty_list_returns_empty(self):
        self.assertEqual(normalize_config_content([]), "")

    def test_dict_is_json_serialized_with_sorted_keys(self):
        result = normalize_config_content({"b": 1, "a": 2})
        self.assertEqual(result, '{"a": 2, "b": 1}')

    def test_dict_normalization_is_key_order_independent(self):
        self.assertEqual(
            normalize_config_content({"b": 1, "a": 2}),
            normalize_config_content({"a": 2, "b": 1}),
        )

    def test_list_is_json_serialized(self):
        result = normalize_config_content([{"b": 1, "a": 2}, {"c": 3}])
        # Nested dicts get key-sorted; list element order preserved.
        self.assertEqual(result, '[{"a": 2, "b": 1}, {"c": 3}]')

    def test_string_is_stripped(self):
        self.assertEqual(normalize_config_content("  hostname foo  \n"), "hostname foo")

    def test_string_without_surrounding_whitespace_is_unchanged(self):
        self.assertEqual(normalize_config_content("hostname foo"), "hostname foo")

    def test_integer_falls_through_to_str(self):
        self.assertEqual(normalize_config_content(42), "42")

    def test_boolean_falls_through_to_str(self):
        # bool() is truthy/falsy distinct from None; the fallback applies.
        self.assertEqual(normalize_config_content(True), "True")


class ComputeConfigHashTestCase(TestCase):
    """Cover ``compute_config_hash`` semantics."""

    def test_returns_64_char_lowercase_hex(self):
        digest = compute_config_hash("hostname foo")
        self.assertEqual(len(digest), 64)
        self.assertTrue(all(c in "0123456789abcdef" for c in digest))

    def test_empty_content_hashes_to_sha256_of_empty_string(self):
        self.assertEqual(compute_config_hash(""), EMPTY_SHA256)
        self.assertEqual(compute_config_hash(None), EMPTY_SHA256)
        self.assertEqual(compute_config_hash({}), EMPTY_SHA256)

    def test_identical_content_produces_identical_hash(self):
        self.assertEqual(
            compute_config_hash({"a": 1, "b": 2}),
            compute_config_hash({"b": 2, "a": 1}),
        )

    def test_different_content_produces_different_hashes(self):
        self.assertNotEqual(
            compute_config_hash({"a": 1}),
            compute_config_hash({"a": 2}),
        )

    def test_string_and_dict_with_same_serialization_match(self):
        # A string that happens to equal the JSON serialization of a dict
        # should hash identically (proves we normalize, not type-fork).
        equivalent_str = json.dumps({"a": 1}, sort_keys=True)
        self.assertEqual(
            compute_config_hash({"a": 1}),
            compute_config_hash(equivalent_str),
        )

    def test_whitespace_is_significant_inside_strings(self):
        # Internal whitespace differs → different hash. Only surrounding
        # whitespace is stripped by ``normalize_config_content``.
        self.assertNotEqual(
            compute_config_hash("hostname foo"),
            compute_config_hash("hostname  foo"),
        )
