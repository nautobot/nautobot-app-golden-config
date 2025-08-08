"""Utility functions for compliance checks on saves in Nautobot Golden Config."""

import re
from collections import defaultdict
from functools import reduce
from operator import getitem


def _parse_index_element_string(index_element_string):
    """Build out dictionary from the index element string."""
    result = {}
    pattern = r"\[\'(.*?)\'\]"
    match = re.findall(pattern, index_element_string)
    if match:
        for inner_key in match[1::]:
            result[inner_key] = ""
    return match, result


def set_nested_value(data, keys, value):
    """
    Recursively sets a value in a nested dictionary, given a list of keys.

    Args:
        data (dict): The nested dictionary to modify.
        keys (list): A list of keys to access the target value.
        value: The value to set.

    Returns:
        None: The function modifies the dictionary in place.  Returns None.
    """
    if not keys:
        return  # Should not happen, but good to have.
    if len(keys) == 1:
        data[keys[0]] = value
    else:
        if keys[0] not in data:
            data[keys[0]] = {}  # Create the nested dictionary if it doesn't exist
        set_nested_value(data[keys[0]], keys[1:], value)


def parse_diff(jdiff_evaluate_response, actual, intended, match_config):
    """Parse jdiff evaluate result into missing and extra dictionaries."""
    extra = {}
    missing = {}

    def process_diff(_map, extra_map, missing_map, previous_key=None):
        for key, value in _map.items():
            if isinstance(value, dict) and "new_value" in value and "old_value" in value:
                extra_map[key] = value["old_value"]
                missing_map[key] = value["new_value"]
            elif isinstance(value, str):
                if "missing" in value:
                    extra_map[key] = actual.get(match_config, {}).get(key)
                if "new" in value:
                    key_chain, _ = _parse_index_element_string(key)
                    new_value = reduce(getitem, key_chain, intended)
                    set_nested_value(missing_map, key_chain[1::], new_value)
            elif isinstance(value, defaultdict):
                if dict(value).get("new"):
                    missing[previous_key][key] = dict(value).get("new", {})
                if dict(value).get("missing"):
                    extra_map[previous_key][key] = dict(value).get("missing", {})
            elif isinstance(value, dict):
                extra_map[key] = {}
                missing_map[key] = {}
                process_diff(value, extra_map[key], missing_map[key], previous_key=key)
        return extra_map, missing_map

    extras, missing = process_diff(jdiff_evaluate_response, extra, missing)
    # Don't like this, but with less the performant way of doing it right now it works to clear out
    # Any empty dicts that are left over from the diff.
    # This is a bit of a hack, but it works for now.
    final_extras = extras.copy()
    final_missing = missing.copy()
    for key, value in extras.items():
        if isinstance(value, dict):
            if not value:
                del final_extras[key]
    for key, value in missing.items():
        if isinstance(value, dict):
            if not value:
                del final_missing[key]
    return final_extras, final_missing
