"""App Config Schema Generator and Validator."""
import json
from importlib import import_module
from os import getenv
from pathlib import Path
from urllib.parse import urlparse

import jsonschema
import toml
from django.conf import settings
from to_json_schema.to_json_schema import SchemaBuilder


def _enrich_object_schema(schema, defaults, required):
    schema["additionalProperties"] = False
    for key, value in schema["properties"].items():
        if required and key in required:
            value["required"] = True
        default_value = defaults and defaults.get(key, None)
        if value["type"] == "object" and "properties" in value:
            _enrich_object_schema(value, default_value, None)
        elif default_value is not None:
            value["default"] = default_value


def _main():
    pyproject = toml.loads(Path("pyproject.toml").read_text())
    url = urlparse(pyproject["tool"]["poetry"]["repository"])
    _, owner, repository = url.path.split("/")
    package_name = pyproject["tool"]["poetry"]["packages"][0]["include"]
    app_config = settings.PLUGINS_CONFIG[package_name]  # type: ignore
    schema_path = Path(package_name) / "app-config-schema.json"
    command = getenv("APP_CONFIG_SCHEMA_COMMAND", "")
    if command == "generate":
        schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": f"https://raw.githubusercontent.com/{owner}/{repository}/develop/{package_name}/app-config-schema.json",
            "$comment": "TBD: Update $id, replace `develop` with the future release tag",
            **SchemaBuilder().to_json_schema(app_config),  # type: ignore
        }
        app_config = import_module(package_name).config
        _enrich_object_schema(schema, app_config.default_settings, app_config.required_settings)
        schema_path.write_text(json.dumps(schema, indent=4) + "\n")
        print(f"\n==================\nGenerated schema:\n\n{schema_path}\n")
        print(
            "WARNING: Review and edit the generated file before committing.\n"
            "\n"
            "Its content is inferred from:\n"
            "\n"
            "- The current configuration in `PLUGINS_CONFIG`\n"
            "- `NautobotAppConfig.default_settings`\n"
            "- `NautobotAppConfig.required_settings`"
        )
    elif command == "validate":
        schema = json.loads(schema_path.read_text())
        jsonschema.validate(app_config, schema)
        print(
            f"\n==================\nValidated configuration using the schema:\n{schema_path}\nConfiguration is valid."
        )
    else:
        raise RuntimeError(f"Unknown command: {command}")


_main()
