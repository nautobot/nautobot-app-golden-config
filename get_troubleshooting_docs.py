"""Generate troubleshooting documentation for each error code."""

import os

from jinja2 import Environment, FileSystemLoader

from nautobot_golden_config.error_codes import ERROR_CODES


def generate_files_from_template(template_file):
    """
    Generates files from a Jinja2 template in the same directory as the script.

    Args:
        template_file (str): Name of the Jinja2 template file.
        output_dir (str): Path to the directory where the output files will be saved.
        data (dict): Data to be passed to the template.
        num_files (int, optional): Number of files to generate. Defaults to 1.
    """
    data = {}
    template_dir = os.path.dirname(os.path.abspath(__file__))
    env = Environment(loader=FileSystemLoader(template_dir), autoescape=True)
    template = env.get_template(template_file)
    for error_code, error in ERROR_CODES.items():
        data["error_code"] = error_code
        data["error"] = error
        output_filename = f"{error_code}.md"  # Customize the filename as needed
        output_filepath = os.path.join(template_dir, "docs", "admin", "troubleshooting", output_filename)
        output_content = template.render(data)

        with open(output_filepath, "w", encoding="utf-8") as doc_file:
            doc_file.write(output_content)


if __name__ == "__main__":
    generate_files_from_template("error_code_template.j2")
