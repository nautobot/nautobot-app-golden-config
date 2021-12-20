"""Jinja2 filters provided by the Nautobot Plugin."""
import os
import re
from typing import List, Iterable

from django_jinja import library


@library.filter
def find_available_files(filepaths: Iterable[str], search_words: Iterable[str], file_extension: str) -> Iterable[str]:
    """
    Find all unique filenames that end with ``search_words`` + ``file_extension`` in all ``filepaths``.

    Args:
        filepaths: The paths to directories where files with ``search_words`` should be inspected.
        search_words: The last word(s) of the file to find in ``filepaths``.
        file_extension: The extension of the files to look for in ``filepaths``.

    Returns:
        list: The unique list of filenames without the file extension.

    Examples:
        >>> os.listdir("templates/ios/c9300")
        ['180_aaa.j2', '200_bgp.j2', ...]
        >>> os.listdir("templates/ios")
        ['100_aaa.j2', '150_dns.j2', '180_aaa', 'c9300', ...]
        >>> filepaths = ["templates/ios/c9300", "templates/ios"]
        >>> search_words = ["aaa", "dns"]
        >>> file_extension = "j2"
        >>> available_files = find_available_files(filepaths, search_words, file_extension)
        >>> available_files
        ['100_aaa.j2', '150_dns.j2', '180_aaa.j2']
    """
    valid_filepaths = [filepath for filepath in filepaths if os.path.isdir(filepath)]
    file_search_patterns = [fr"^(.*{word})\.{file_extension}$" for word in search_words]
    re_file_search = re.compile(r"|".join(file_search_patterns))
    matching_files = set()
    for filepath in valid_filepaths:
        for directory_item in os.listdir(filepath):
            re_file_search_match = re_file_search.match(directory_item)
            if re_file_search_match:
                matching_files.add(re_file_search_match.group())

    return list(matching_files)


@library.filter
def collect_preferred_files(path_preferences: Iterable[str], filenames: Iterable[str]) -> List[str]:
    """
    Collect the most preferred file paths that exist on the filesystem.

    Args:
        path_preferences: The list of paths in their preferred order.
        filenames: The names of the files to look for.

    Returns:
        list: The most preferred path for each filename in filenames

    Examples:
        >>> os.listdir("templates/ios/c9300")
        ['180_aaa.j2', 200_bgp.j2', ...]
        >>> os.listdir("templates/ios")
        ['100_aaa.j2', '150_dns.j2', '180_aaa', 'c9300', ...]
        >>> path_preferences = ["templates/ios/c9300", "templates/ios"]
        >>> filenames = ["100_aaa.j2", "150_dns.j2", "180_aaa.j2"]
        >>> templates = collect_preferred_files(path_preferences, filenames)
        >>> templates
        ['.../templates/ios/100_aaa.j2', '.../templates/ios/150_dns.j2', '.../templates/ios/c9300/180_aaa.j2']
    """
    return [collect_preferred_file(path_preferences, filename) for filename in filenames]


@library.filter
def collect_preferred_file(path_preferences: Iterable[str], filename: str) -> str:
    """
    Find the most preferred file that exists on the filesystem.

    Args:
        path_preferences: The list of paths in their preferred order.
        filename: The name of the file to look for.

    Returns:
        str: Then absolute path to the most preferred template.

    Raises:
        FileNotFoundError: When none of the paths in ``path_preferences`` contains a file named ``filename``.

    Examples
        >>> os.listdir("templates/ios/c9300")
        ['180_aaa.j2', 200_bgp.j2', ...]
        >>> os.listdir("templates/ios")
        ['100_aaa.j2', '150_dns.j2', '180_aaa', 'c9300', ...]
        >>> path_preferences = ["templates/ios/c9300", "templates/ios"]
        >>> filename = ["180_aaa.j2"]
        >>> template = collect_preferred_file(path_preferences, filename)
        >>> template
        '.../templates/ios/c9300/180_aaa.j2'
    """
    for filepath in path_preferences:
        absolute_path = os.path.join(os.path.abspath(filepath), filename)
        if os.path.isfile(absolute_path):
            return absolute_path

    raise FileNotFoundError(f"Could not find file with name {filename} in {path_preferences}")
