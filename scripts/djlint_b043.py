"""rule B043: Active class should be applied to anchor tags instead of list items within navigation tabs."""

from __future__ import annotations

from typing import TYPE_CHECKING

import regex as re

from djlint.helpers import (
    inside_ignored_linter_block,
    inside_ignored_rule,
    overlaps_ignored_block,
)
from djlint.lint import get_line

if TYPE_CHECKING:
    from typing_extensions import Any
    from djlint.settings import Config
    from djlint.types import LintError


def run(
    rule: dict[str, Any],
    config: Config,
    html: str,
    filepath: str,
    line_ends: list[dict[str, int]],
    *args: Any,
    **kwargs: Any,
) -> tuple[LintError, ...]:
    """Add nav-item class to list items within navigation tabs."""
    errors: list[LintError] = []

    # Check for <ul class="nav nav-tabs">
    for ul_match in re.finditer(r"<ul\s+class=(['\"])(.*?)\1[^>]*>", html, flags=re.IGNORECASE):
        if "nav-tabs" in ul_match.group(2).lower():
            ul_start = ul_match.start()
            closing_ul_match = re.search(r"</ul>", html[ul_start:], flags=re.IGNORECASE)
            if closing_ul_match:
                ul_end_content = ul_start + closing_ul_match.start()
                ul_content = html[ul_start : ul_end_content]

                # Check for <a> tags with class="active" but missing nav-link
                for a_match in re.finditer(r"<a[^>]*class=(['\"])(.*?)\1[^>]*>", ul_content, flags=re.IGNORECASE):
                    a_classes = a_match.group(2)
                    if "active" in a_classes.split() and "nav-link" not in a_classes.split():
                        a_start_relative = a_match.start()
                        a_start_absolute = ul_start + a_start_relative
                        errors.append(
                            {
                                "code": rule["name"],
                                "line": get_line(a_start_absolute, line_ends),
                                "match": html[a_start_absolute : a_start_absolute + 40].strip()[:40],
                                "message": "Active nav links must use class=\"nav-link active\".",
                            }
                        )

    # Check within {% block extra_nav_tabs %}
    for block_match in re.finditer(
        r"{%\s+block\s+extra_nav_tabs\s*%}(.*?){%\s+endblock\s+extra_nav_tabs\s*%}",
        html,
        flags=re.DOTALL | re.IGNORECASE,
    ):
        block_content = block_match.group(1)
        block_start = block_match.start()

        for a_match in re.finditer(r"<a[^>]*class=(['\"])(.*?)\1[^>]*>", block_content, flags=re.IGNORECASE):
            a_classes = a_match.group(2)
            if "active" in a_classes.split() and "nav-link" not in a_classes.split():
                a_start_relative = a_match.start()
                a_start_absolute = block_start + a_start_relative + len(block_match.group(0).split(block_content)[0])
                errors.append(
                    {
                        "code": rule["name"],
                        "line": get_line(a_start_absolute, line_ends),
                        "match": a_match.group(0).strip()[:40],
                        "message": "Active nav links must use class=\"nav-link active\".",
                    }
                )

    return tuple(
        error
        for error in errors
    )
