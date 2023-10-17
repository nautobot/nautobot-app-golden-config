"""Tasks for use with Invoke.

Copyright (c) 2023, Network to Code, LLC
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

import os

from invoke.collection import Collection
from invoke.tasks import task as invoke_task


def is_truthy(arg):
    """Convert "truthy" strings into Booleans.

    Examples:
        >>> is_truthy('yes')
        True
    Args:
        arg (str): Truthy string (True values are y, yes, t, true, on and 1; false values are n, no,
        f, false, off and 0. Raises ValueError if val is anything else.
    """
    if isinstance(arg, bool):
        return arg

    val = str(arg).lower()
    if val in ("y", "yes", "t", "true", "on", "1"):
        return True
    elif val in ("n", "no", "f", "false", "off", "0"):
        return False
    else:
        raise ValueError(f"Invalid truthy value: `{arg}`")


# Use pyinvoke configuration for default values, see http://docs.pyinvoke.org/en/stable/concepts/configuration.html
# Variables may be overwritten in invoke.yml or by the environment variables INVOKE_NAUTOBOT_GOLDEN_CONFIG_xxx
namespace = Collection("nautobot_golden_config")
namespace.configure(
    {
        "nautobot_golden_config": {
            "nautobot_ver": "2.0.0",
            "project_name": "nautobot-golden-config",
            "python_ver": "3.11",
            "local": False,
            "compose_dir": os.path.join(os.path.dirname(__file__), "development"),
            "compose_files": [
                "docker-compose.base.yml",
                "docker-compose.redis.yml",
                "docker-compose.postgres.yml",
                "docker-compose.dev.yml",
            ],
            "compose_http_timeout": "86400",
        }
    }
)


def _is_compose_included(context, name):
    return f"docker-compose.{name}.yml" in context.nautobot_golden_config.compose_files


def task(function=None, *args, **kwargs):
    """Task decorator to override the default Invoke task decorator and add each task to the invoke namespace."""

    def task_wrapper(function=None):
        """Wrapper around invoke.task to add the task to the namespace as well."""
        if args or kwargs:
            task_func = invoke_task(*args, **kwargs)(function)
        else:
            task_func = invoke_task(function)
        namespace.add_task(task_func)
        return task_func

    if function:
        # The decorator was called with no arguments
        return task_wrapper(function)
    # The decorator was called with arguments
    return task_wrapper


def docker_compose(context, command, **kwargs):
    """Helper function for running a specific docker compose command with all appropriate parameters and environment.

    Args:
        context (obj): Used to run specific commands
        command (str): Command string to append to the "docker compose ..." command, such as "build", "up", etc.
        **kwargs: Passed through to the context.run() call.
    """
    build_env = {
        # Note: 'docker compose logs' will stop following after 60 seconds by default,
        # so we are overriding that by setting this environment variable.
        "COMPOSE_HTTP_TIMEOUT": context.nautobot_golden_config.compose_http_timeout,
        "NAUTOBOT_VER": context.nautobot_golden_config.nautobot_ver,
        "PYTHON_VER": context.nautobot_golden_config.python_ver,
        **kwargs.pop("env", {}),
    }
    compose_command_tokens = [
        "docker compose",
        f"--project-name {context.nautobot_golden_config.project_name}",
        f'--project-directory "{context.nautobot_golden_config.compose_dir}"',
    ]

    for compose_file in context.nautobot_golden_config.compose_files:
        compose_file_path = os.path.join(context.nautobot_golden_config.compose_dir, compose_file)
        compose_command_tokens.append(f' -f "{compose_file_path}"')

    compose_command_tokens.append(command)

    # If `service` was passed as a kwarg, add it to the end.
    service = kwargs.pop("service", None)
    if service is not None:
        compose_command_tokens.append(service)

    print(f'Running docker compose command "{command}"')
    compose_command = " ".join(compose_command_tokens)

    return context.run(compose_command, env=build_env, **kwargs)


def run_command(context, command, **kwargs):
    """Wrapper to run a command locally or inside the nautobot container."""
    if is_truthy(context.nautobot_golden_config.local):
        context.run(command, **kwargs)
    else:
        # Check if nautobot is running, no need to start another nautobot container to run a command
        docker_compose_status = "ps --services --filter status=running"
        results = docker_compose(context, docker_compose_status, hide="out")
        if "nautobot" in results.stdout:
            compose_command = f"exec nautobot {command}"
        else:
            compose_command = f"run --rm --entrypoint '{command}' nautobot"

        pty = kwargs.pop("pty", True)

        docker_compose(context, compose_command, pty=pty, **kwargs)


# ------------------------------------------------------------------------------
# BUILD
# ------------------------------------------------------------------------------
@task(
    help={
        "force_rm": "Always remove intermediate containers",
        "cache": "Whether to use Docker's cache when building the image (defaults to enabled)",
    }
)
def build(context, force_rm=False, cache=True):
    """Build Nautobot docker image."""
    command = "build"

    if not cache:
        command += " --no-cache"
    if force_rm:
        command += " --force-rm"

    print(f"Building Nautobot with Python {context.nautobot_golden_config.python_ver}...")
    docker_compose(context, command)


@task
def generate_packages(context):
    """Generate all Python packages inside docker and copy the file locally under dist/."""
    command = "poetry build"
    run_command(context, command)


@task(
    help={
        "check": (
            "If enabled, check for outdated dependencies in the poetry.lock file, "
            "instead of generating a new one. (default: disabled)"
        )
    }
)
def lock(context, check=False):
    """Generate poetry.lock inside the Nautobot container."""
    run_command(context, f"poetry {'check' if check else 'lock --no-update'}")


# ------------------------------------------------------------------------------
# START / STOP / DEBUG
# ------------------------------------------------------------------------------
@task(help={"service": "If specified, only affect this service."})
def debug(context, service=""):
    """Start specified or all services and its dependencies in debug mode."""
    print(f"Starting {service} in debug mode...")
    docker_compose(context, "up", service=service)


@task(help={"service": "If specified, only affect this service."})
def start(context, service=""):
    """Start specified or all services and its dependencies in detached mode."""
    print("Starting Nautobot in detached mode...")
    docker_compose(context, "up --detach", service=service)


@task(help={"service": "If specified, only affect this service."})
def restart(context, service=""):
    """Gracefully restart specified or all services."""
    print("Restarting Nautobot...")
    docker_compose(context, "restart", service=service)


@task(help={"service": "If specified, only affect this service."})
def stop(context, service=""):
    """Stop specified or all services, if service is not specified, remove all containers."""
    print("Stopping Nautobot...")
    docker_compose(context, "stop" if service else "down --remove-orphans", service=service)


@task
def destroy(context):
    """Destroy all containers and volumes."""
    print("Destroying Nautobot...")
    docker_compose(context, "down --remove-orphans --volumes")


@task
def export(context):
    """Export docker compose configuration to `compose.yaml` file.

    Useful to:

    - Debug docker compose configuration.
    - Allow using `docker compose` command directly without invoke.
    """
    docker_compose(context, "convert > compose.yaml")


@task(name="ps", help={"all": "Show all, including stopped containers"})
def ps_task(context, all=False):
    """List containers."""
    docker_compose(context, f"ps {'--all' if all else ''}")


@task
def vscode(context):
    """Launch Visual Studio Code with the appropriate Environment variables to run in a container."""
    command = "code nautobot.code-workspace"

    context.run(command)


@task(
    help={
        "service": "If specified, only display logs for this service (default: all)",
        "follow": "Flag to follow logs (default: False)",
        "tail": "Tail N number of lines (default: all)",
    }
)
def logs(context, service="", follow=False, tail=0):
    """View the logs of a docker compose service."""
    command = "logs "

    if follow:
        command += "--follow "
    if tail:
        command += f"--tail={tail} "

    docker_compose(context, command, service=service)


# ------------------------------------------------------------------------------
# ACTIONS
# ------------------------------------------------------------------------------
@task(help={"file": "Python file to execute"})
def nbshell(context, file=""):
    """Launch an interactive nbshell session."""
    command = [
        "nautobot-server",
        "nbshell",
        f"< '{file}'" if file else "",
    ]
    run_command(context, " ".join(command), pty=not bool(file))


@task
def shell_plus(context):
    """Launch an interactive shell_plus session."""
    command = "nautobot-server shell_plus"
    run_command(context, command)


@task
def cli(context):
    """Launch a bash shell inside the Nautobot container."""
    run_command(context, "bash")


@task(
    help={
        "user": "name of the superuser to create (default: admin)",
    }
)
def createsuperuser(context, user="admin"):
    """Create a new Nautobot superuser account (default: "admin"), will prompt for password."""
    command = f"nautobot-server createsuperuser --username {user}"

    run_command(context, command)


@task(
    help={
        "name": "name of the migration to be created; if unspecified, will autogenerate a name",
    }
)
def makemigrations(context, name=""):
    """Perform makemigrations operation in Django."""
    command = "nautobot-server makemigrations nautobot_golden_config"

    if name:
        command += f" --name {name}"

    run_command(context, command)


@task
def migrate(context):
    """Perform migrate operation in Django."""
    command = "nautobot-server migrate"

    run_command(context, command)


@task(help={})
def post_upgrade(context):
    """
    Performs Nautobot common post-upgrade operations using a single entrypoint.

    This will run the following management commands with default settings, in order:

    - migrate
    - trace_paths
    - collectstatic
    - remove_stale_contenttypes
    - clearsessions
    - invalidate all
    """
    command = "nautobot-server post_upgrade"

    run_command(context, command)


@task(
    help={
        "service": "Docker compose service name to run command in (default: nautobot).",
        "command": "Command to run (default: bash).",
        "file": "File to run command with (default: empty)",
    },
)
def exec(context, service="nautobot", command="bash", file=""):
    """Launch a command inside the running container (defaults to bash shell inside nautobot container)."""
    command = [
        "exec",
        "--",
        service,
        command,
        f"< '{file}'" if file else "",
    ]
    docker_compose(context, " ".join(command), pty=not bool(file))


@task(
    help={
        "db-name": "Database name (default: Nautobot database)",
        "input-file": "SQL file to execute and quit (default: empty, start interactive CLI)",
        "output-file": "Ouput file, overwrite if exists (default: empty, output to stdout)",
        "query": "SQL command to execute and quit (default: empty)",
    }
)
def dbshell(context, db_name="", input_file="", output_file="", query=""):
    """Start database CLI inside the running `db` container.

    Doesn't use `nautobot-server dbshell`, using started `db` service container only.
    """
    if input_file and query:
        raise ValueError("Cannot specify both, `input_file` and `query` arguments")
    if output_file and not (input_file or query):
        raise ValueError("`output_file` argument requires `input_file` or `query` argument")

    env = {}
    if query:
        env["_SQL_QUERY"] = query

    command = [
        "exec",
        "--env=_SQL_QUERY" if query else "",
        "-- db sh -c '",
    ]

    if _is_compose_included(context, "mysql"):
        command += [
            "mysql",
            "--user=$MYSQL_USER",
            "--password=$MYSQL_PASSWORD",
            f"--database={db_name or '$MYSQL_DATABASE'}",
        ]
    elif _is_compose_included(context, "postgres"):
        command += [
            "psql",
            "--username=$POSTGRES_USER",
            f"--dbname={db_name or '$POSTGRES_DB'}",
        ]
    else:
        raise ValueError("Unsupported database backend.")

    command += [
        "'",
        '<<<"$_SQL_QUERY"' if query else "",
        f"< '{input_file}'" if input_file else "",
        f"> '{output_file}'" if output_file else "",
    ]

    docker_compose(context, " ".join(command), env=env, pty=not (input_file or output_file or query))


@task(
    help={
        "input-file": "SQL dump file to replace the existing database with. This can be generated using `invoke backup-db` (default: `dump.sql`).",
    }
)
def import_db(context, input_file="dump.sql"):
    """Stop Nautobot containers and replace the current database with the dump into the running `db` container."""
    docker_compose(context, "stop -- nautobot worker")

    command = ["exec -- db sh -c '"]

    if _is_compose_included(context, "mysql"):
        command += [
            "mysql",
            "--database=$MYSQL_DATABASE",
            "--user=$MYSQL_USER",
            "--password=$MYSQL_PASSWORD",
        ]
    elif _is_compose_included(context, "postgres"):
        command += [
            "psql",
            "--username=$POSTGRES_USER",
            "postgres",
        ]
    else:
        raise ValueError("Unsupported database backend.")

    command += [
        "'",
        f"< '{input_file}'",
    ]

    docker_compose(context, " ".join(command), pty=False)

    print("Database import complete, you can start Nautobot now: `invoke start`")


@task(
    help={
        "db-name": "Database name to backup (default: Nautobot database)",
        "output-file": "Ouput file, overwrite if exists (default: `dump.sql`)",
        "readable": "Flag to dump database data in more readable format (default: `True`)",
    }
)
def backup_db(context, db_name="", output_file="dump.sql", readable=True):
    """Dump database into `output_file` file from running `db` container."""
    command = ["exec -- db sh -c '"]

    if _is_compose_included(context, "mysql"):
        command += [
            "mysqldump",
            "--user=root",
            "--password=$MYSQL_ROOT_PASSWORD",
            "--add-drop-database",
            "--skip-extended-insert" if readable else "",
            "--databases",
            db_name if db_name else "$MYSQL_DATABASE",
        ]
    elif _is_compose_included(context, "postgres"):
        command += [
            "pg_dump",
            "--clean",
            "--create",
            "--if-exists",
            "--username=$POSTGRES_USER",
            f"--dbname={db_name or '$POSTGRES_DB'}",
            "--inserts" if readable else "",
        ]
    else:
        raise ValueError("Unsupported database backend.")

    command += [
        "'",
        f"> '{output_file}'",
    ]

    docker_compose(context, " ".join(command), pty=False)

    print(50 * "=")
    print("The database backup has been successfully completed and saved to the following file:")
    print(output_file)
    print("You can import this database backup with the following command:")
    print(f"invoke import-db --input-file '{output_file}'")
    print(50 * "=")


# ------------------------------------------------------------------------------
# DOCS
# ------------------------------------------------------------------------------
@task
def docs(context):
    """Build and serve docs locally for development."""
    command = "mkdocs serve -v"

    if is_truthy(context.nautobot_golden_config.local):
        print(">>> Serving Documentation at http://localhost:8001")
        run_command(context, command)
    else:
        start(context, service="docs")


@task
def build_and_check_docs(context):
    """Build documentation to be available within Nautobot."""
    command = "mkdocs build --no-directory-urls --strict"
    run_command(context, command)


@task(name="help")
def help_task(context):
    """Print the help of available tasks."""
    import tasks  # pylint: disable=all

    root = Collection.from_module(tasks)
    for task_name in sorted(root.task_names):
        print(50 * "-")
        print(f"invoke {task_name} --help")
        context.run(f"invoke {task_name} --help")


# ------------------------------------------------------------------------------
# TESTS
# ------------------------------------------------------------------------------
@task(
    help={
        "autoformat": "Apply formatting recommendations automatically, rather than failing if formatting is incorrect.",
    }
)
def black(context, autoformat=False):
    """Check Python code style with Black."""
    if autoformat:
        black_command = "black"
    else:
        black_command = "black --check --diff"

    command = f"{black_command} ."

    run_command(context, command)


@task
def flake8(context):
    """Check for PEP8 compliance and other style issues."""
    command = "flake8 . --config .flake8"
    run_command(context, command)


@task
def hadolint(context):
    """Check Dockerfile for hadolint compliance and other style issues."""
    command = "hadolint development/Dockerfile"
    run_command(context, command)


@task
def pylint(context):
    """Run pylint code analysis."""
    command = 'pylint --init-hook "import nautobot; nautobot.setup()" --rcfile pyproject.toml nautobot_golden_config'
    run_command(context, command)


@task
def pydocstyle(context):
    """Run pydocstyle to validate docstring formatting adheres to NTC defined standards."""
    # We exclude the /migrations/ directory since it is autogenerated code
    command = "pydocstyle ."
    run_command(context, command)


@task
def bandit(context):
    """Run bandit to validate basic static code security analysis."""
    command = "bandit --recursive . --configfile .bandit.yml"
    run_command(context, command)


@task
def yamllint(context):
    """Run yamllint to validate formatting adheres to NTC defined YAML standards.

    Args:
        context (obj): Used to run specific commands
    """
    command = "yamllint . --format standard"
    run_command(context, command)


@task
def check_migrations(context):
    """Check for missing migrations."""
    command = "nautobot-server makemigrations --dry-run --check"

    run_command(context, command)


@task(
    help={
        "keepdb": "save and re-use test database between test runs for faster re-testing.",
        "label": "specify a directory or module to test instead of running all Nautobot tests",
        "failfast": "fail as soon as a single test fails don't run the entire test suite",
        "buffer": "Discard output from passing tests",
        "pattern": "Run specific test methods, classes, or modules instead of all tests",
        "verbose": "Enable verbose test output.",
    }
)
def unittest(
    context,
    keepdb=False,
    label="nautobot_golden_config",
    failfast=False,
    buffer=True,
    pattern="",
    verbose=False,
):
    """Run Nautobot unit tests."""
    command = f"coverage run --module nautobot.core.cli test {label}"

    if keepdb:
        command += " --keepdb"
    if failfast:
        command += " --failfast"
    if buffer:
        command += " --buffer"
    if pattern:
        command += f" -k='{pattern}'"
    if verbose:
        command += " --verbosity 2"

    run_command(context, command)


@task
def unittest_coverage(context):
    """Report on code test coverage as measured by 'invoke unittest'."""
    command = "coverage report --skip-covered --include 'nautobot_golden_config/*' --omit *migrations*"

    run_command(context, command)


@task(
    help={
        "failfast": "fail as soon as a single test fails don't run the entire test suite. (default: False)",
        "keepdb": "Save and re-use test database between test runs for faster re-testing. (default: False)",
        "lint-only": "Only run linters; unit tests will be excluded. (default: False)",
    }
)
def tests(context, failfast=False, keepdb=False, lint_only=False):
    """Run all tests for this plugin."""
    # If we are not running locally, start the docker containers so we don't have to for each test
    if not is_truthy(context.nautobot_golden_config.local):
        print("Starting Docker Containers...")
        start(context)
    # Sorted loosely from fastest to slowest
    print("Running black...")
    black(context)
    print("Running flake8...")
    flake8(context)
    print("Running bandit...")
    bandit(context)
    print("Running pydocstyle...")
    pydocstyle(context)
    print("Running yamllint...")
    yamllint(context)
    print("Running poetry check...")
    lock(context, check=True)
    print("Running migrations check...")
    check_migrations(context)
    print("Running pylint...")
    pylint(context)
    print("Running mkdocs...")
    build_and_check_docs(context)
    if not lint_only:
        print("Running unit tests...")
        unittest(context, failfast=failfast, keepdb=keepdb)
        unittest_coverage(context)
    print("All tests have passed!")
