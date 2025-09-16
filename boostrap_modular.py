import re
from bs4 import BeautifulSoup
import os
import argparse

# Finish adding fixers
# Add count of all issues found and fixed
# Call out items that could not be fixed
# Give it a nautobot app directory and have it find the templates to fix.
# Repo_root/nautobot-golden-config/templates/nautobot-app-golden-config/*html_files*

# --- Rule Functions (BeautifulSoup-based) ---

def _fix_breadcrumb_items(soup: BeautifulSoup, stats: dict):
    """
    Adds 'breadcrumb-item' class to <li> elements within <ol class="breadcrumb">.
    Modifies the soup object directly.
    """
    for ol_tag in soup.find_all('ol', class_=re.compile(r'\bbreadcrumb\b', re.IGNORECASE)):
        for li_tag in ol_tag.find_all('li'):
            if not li_tag.has_attr('class') or 'breadcrumb-item' not in li_tag['class']:
                if not li_tag.has_attr('class'):
                    li_tag['class'] = []
                li_tag['class'].append('breadcrumb-item')
                stats['breadcrumb_items'] += 1
                print(f"DEBUG: Added 'breadcrumb-item' to <li> in <ol.breadcrumb>: {li_tag.prettify().strip().splitlines()[0]}...")

def _fix_nav_tabs_items(soup: BeautifulSoup, stats: dict):
    """
    Adds 'nav-item' class to <li> elements within <ul class="nav nav-tabs">.
    Modifies the soup object directly.
    """
    for ul_tag in soup.find_all('ul', class_=lambda c: c and 'nav' in c and 'nav-tabs' in c.split()):
        for li_tag in ul_tag.find_all('li'):
            if not li_tag.has_attr('class') or 'nav-item' not in li_tag['class']:
                if not li_tag.has_attr('class'):
                    li_tag['class'] = []
                li_tag['class'].append('nav-item')
                stats['nav_items'] += 1
                print(f"DEBUG: Added 'nav-item' to <li> in <ul.nav.nav-tabs>: {li_tag.prettify().strip().splitlines()[0]}...")

def _replace_classes(html_string: str, replacements: dict, stats: dict) -> str:
    """
    Replaces class names in html_string according to the replacements dict.
    Each key is replaced with its value using regex word boundaries, case-insensitive.
    """
    for search, replace in replacements.items():
        if search in html_string:  # Quick check to avoid regex if not present
            html_string = re.sub(rf'\\b{re.escape(search)}\\b', replace, html_string, flags=re.IGNORECASE)
            stats['replacements'] += 1
            print(f"DEBUG: Replaced '{search}' with '{replace}'.")
    return html_string

# --- Rule Function (Regex-based for specific block content) ---

def _fix_extra_breadcrumbs_block(html_string: str, stats: dict) -> str:
    """
    Finds {% block extra_breadcrumbs %} blocks, parses their inner content
    with BeautifulSoup, adds 'breadcrumb-item' to <li>, and reconstructs the block.
    Operates on the HTML string.
    """
    block_pattern = re.compile(
        r'({%\s*block\s+extra_breadcrumbs\s*%})'
        r'(.*?)'
        r'({%\s*endblock\s+extra_breadcrumbs\s*%})',
        flags=re.DOTALL | re.IGNORECASE
    )

    def process_match(match):
        block_start_tag = match.group(1)
        block_inner_content = match.group(2)
        block_end_tag = match.group(3)

        inner_soup = BeautifulSoup(block_inner_content, 'html.parser')
        for li_tag in inner_soup.find_all('li'):
            if not li_tag.has_attr('class') or 'breadcrumb-item' not in li_tag['class']:
                if not li_tag.has_attr('class'):
                    li_tag['class'] = []
                li_tag['class'].append('breadcrumb-item')
                stats['extra_breadcrumbs'] += 1
                print(f"DEBUG: Added 'breadcrumb-item' to <li> within 'extra_breadcrumbs' block: {li_tag.prettify().strip().splitlines()[0]}...")

        new_inner_content_str = str(inner_soup)
        return f"{block_start_tag}{new_inner_content_str}{block_end_tag}"

    # Apply the regex substitution. `sub` with a function handles multiple matches.
    return block_pattern.sub(process_match, html_string)


# --- Main Conversion Function ---

def convert_bootstrap_classes(html_input: str) -> (str, dict):
    """
    Applies various Bootstrap 3 to 5 conversion rules to the HTML content.
    """
    current_html = html_input # Start with the original HTML

    # Initialize stats
    stats = {
        'replacements': 0,
        'extra_breadcrumbs': 0,
        'breadcrumb_items': 0,
        'nav_items': 0,
    }

    # --- Stage 1: Apply rules that work directly on the HTML string (simple string/regex replacements) ---
    replacements = {
        'pull-left': 'float-start',
        'pull-right': 'float-end',
        'center-block': 'mx-auto',  # Bootstrap 5 uses mx-auto for centering
        'data-toggle': 'data-bs-toggle',  # Bootstrap 5 uses data-bs-* attributes
        'data-dismiss': 'data-bs-dismiss',  # Bootstrap 5 uses data-bs-* attributes
        'data-target': 'data-bs-target',  # Bootstrap 5 uses data-bs-* attributes
        'data-title': 'data-bs-title',  # Bootstrap 5 uses data-bs-* attributes
        'btn-default': 'btn-secondary',
        'close': 'btn-close',  # Bootstrap 5 uses btn-close for close buttons
        'btn-xs': 'btn-sm',  # Bootstrap 5 does not have btn-xs, use btn-sm instead


        # Add more replacements here as needed
    }
    current_html = _replace_classes(current_html, replacements, stats)
    current_html = _fix_extra_breadcrumbs_block(current_html, stats) # This also works on the string

    # --- Stage 2: Parse with BeautifulSoup for DOM-based modifications ---
    # After string-based replacements, parse the current HTML to a BeautifulSoup object
    # for more complex DOM manipulations.
    soup = BeautifulSoup(current_html, 'html.parser')

    # Apply BeautifulSoup-based rules
    _fix_breadcrumb_items(soup, stats)
    _fix_nav_tabs_items(soup, stats)

    # Convert the modified BeautifulSoup object back to a string
    final_html = str(soup), stats

    return final_html


# --- File Processing ---

def fix_html_files_in_directory(directory: str):
    """
    Recursively finds all .html files in the given directory, applies convert_bootstrap_classes,
    and overwrites each file with the fixed content.
    """

    totals = {k: 0 for k in ['replacements', 'extra_breadcrumbs', 'breadcrumb_items', 'nav_items']}

    for root, _, files in os.walk(directory):
        for filename in files:
            if filename.lower().endswith('.html'):
                file_path = os.path.join(root, filename)
                print(f"Processing: {file_path}")
                with open(file_path, 'r', encoding='utf-8') as f:
                    original_content = f.read()

                fixed_content, stats = convert_bootstrap_classes(original_content)

                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(fixed_content)
                print(f"Fixed: {file_path}\n")

                print(f"→ {os.path.relpath(file_path, directory)}: "
                      f"{stats['replacements']} class replacements, "
                      f"{stats['extra_breadcrumbs']} extra-breadcrumbs, "
                      f"{stats['breadcrumb_items']} breadcrumb-items, "
                      f"{stats['nav_items']} nav-items\n")

                for k, v in stats.items():
                    totals[k] += v

    # Global summary
    total_issues = sum(totals.values())
    print("=== Global Summary ===")
    print(f"Total issues fixed: {total_issues}")
    print(f"- Class replacements:          {totals['replacements']}")
    print(f"- Extra-breadcrumb fixes:      {totals['extra_breadcrumbs']}")
    print(f"- <li> in <ol.breadcrumb>:     {totals['breadcrumb_items']}")
    print(f"- <li> in <ul.nav-tabs>:       {totals['nav_items']}")


def find_template_dir_from_nautobot_app(app_dir: str) -> str:
    """
    Given a Nautobot app directory, tries to find the template directory.
    E.g., if given "nautobot-golden-config", it looks for:
        nautobot-golden-config/templates/

    Returns the path if found, otherwise raises an error.
    """
    templates_path = os.path.join(app_dir, 'templates')
    print(templates_path)

    if not os.path.exists(templates_path) or not os.path.isdir(templates_path):
        raise FileNotFoundError(f"No 'templates/' directory found in {app_dir}")

    return templates_path

# --- Example Usage ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bootstrap 3 to 5 HTML fixer.")
    parser.add_argument('--fix-dir', type=str, help='Directory to recursively fix all .html files in place.')
    parser.add_argument('--nautobot-app-dir', type=str, help='Nautobot app directory to find templates folder.')
    args = parser.parse_args()

    if args.fix_dir:
        fix_html_files_in_directory(args.fix_dir)
    elif args.nautobot_app_dir:
        try:
            template_dir = find_template_dir_from_nautobot_app(args.nautobot_app_dir)
            print(f"Found template directory: {template_dir}")
            fix_html_files_in_directory(template_dir)
        except FileNotFoundError as e:
            print(f"Error: {e}")
    else: # need to switch later for an error message if no args are provided.
        template_content = """
                <!DOCTYPE html>
                <html>
                <head>
                    <title>My Page</title>
                    <style>
                        .pull-left { float: left; }
                    </style>
                </head>
                <body>
                    <div class="header pull-left">
                        <h1>Welcome</h1>
                    </div>

                    <ol class="breadcrumb">
                        <li>Home</li>
                        <li class="breadcrumb-item">Category</li>
                        <li>Product {% if some_condition %} Detail {% endif %}</li>
                        <li class="other-class">Another Item</li>
                        <li>{{ variable_name }}</li>
                    </ol>

                    <ul class="nav nav-tabs">
                        <li><a href="#tab1">Tab One</a></li>
                        <li class="active"><a href="#tab2">Tab Two</a></li>
                        <li>Item {{ some_var }}</li>
                    </ul>

                    <p>Some content with a <button class="btn btn-default">Default Button</button> and another <button class="btn btn-lg btn-default">Large Default</button>.</p>

                    {% block extra_breadcrumbs %}
                        <li>Extra Breadcrumb Item A</li>
                        <li class="breadcrumb-item">Another Extra A</li>
                        <li>{% include 'partial_a.html' %}</li>
                    {% endblock extra_breadcrumbs %}

                    Some other content.

                    <p class="text-right pull-left">This text should float start.</p>

                    {% block breadcrumbs %}
                        <ol class="breadcrumb">
                            <li>Main Breadcrumb</li>
                            <li class="test">Test Item</li>
                        </ol>
                    {% endblock breadcrumbs %}

                    {% block extra_breadcrumbs %}
                        <li>Extra Breadcrumb Item B</li>
                        <li class="foo">Another Extra B</li>
                    {% endblock extra_breadcrumbs %}

                    <div>
                        <ol class="some-other-list">
                            <li>Not a breadcrumb</li>
                        </ol>
                    </div>
                </body>
                </html>
                """

        print("--- Original HTML ---")
        print(template_content)

        fixed_html_output, stats = convert_bootstrap_classes(template_content)

        print("\n--- Fixed HTML Output ---")
        print(fixed_html_output)

        print("\n--- Stats ---")
        print(stats)

        print("\n--- Testing with a clean template ---")
        clean_template = """
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Clean Test</title>
                </head>
                <body>
                    <ol class="breadcrumb">
                        <li class="breadcrumb-item">Home</li>
                    </ol>
                    <ul class="nav nav-tabs">
                        <li class="nav-item"><a href="#">Good Tab</a></li>
                    </ul>
                    <div class="float-start">No pull-left here.</div>
                    <button class="btn btn-secondary">No default here</button>
                    {% block extra_breadcrumbs %}
                        <ul>
                            <li class="breadcrumb-item">Already Good</li>
                        </ul>
                    {% endblock extra_breadcrumbs %}
                </body>
                </html>
                """
        fixed_clean_html_output = convert_bootstrap_classes(clean_template)
        print("\n--- Fixed Clean HTML Output (should be mostly unchanged) ---")
        print(fixed_clean_html_output)