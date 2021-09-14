"""Tasks for use with Invoke."""

import os
from distutils.util import strtobool
from invoke import Collection, task

PYTHON_VER = os.getenv("PYTHON_VER", "3.7")
NAUTOBOT_VER = os.getenv("NAUTOBOT_VER", "1.0.1")
NAUTOBOT_SRC_URL = os.getenv("NAUTOBOT_SRC_URL", f"https://github.com/nautobot/nautobot/archive/{NAUTOBOT_VER}.tar.gz")

# Name of the docker image/container
NAME = os.getenv("IMAGE_NAME", "nautobot-golden-config")
PWD = os.getcwd()

COMPOSE_FILE = "development/docker-compose.yml"
COMPOSE_OVERRIDE = "docker-compose.override.yml"
BUILD_NAME = "nautobot_golden_config"

DEFAULT_ENV = {
    "NAUTOBOT_VER": NAUTOBOT_VER,
    "PYTHON_VER": PYTHON_VER,
    "NAUTOBOT_SRC_URL": NAUTOBOT_SRC_URL,
}

COMPOSE_APPEND = ""
if os.path.isfile(COMPOSE_OVERRIDE):
    COMPOSE_APPEND = f"-f {COMPOSE_OVERRIDE}"
COMPOSE_COMMAND = f"docker-compose -f {COMPOSE_FILE} {COMPOSE_APPEND} -p {BUILD_NAME}"

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
    return bool(strtobool(arg))

environment = DEFAULT_ENV

namespace = Collection("nautobot_golden_config")
namespace.configure(
    {
        "nautobot_golden_config": {
            "local": False,
        }
    }
)


def docker_compose(context, command, **kwargs):
    """Helper function for running a specific docker-compose command with all appropriate parameters and environment.

    Args:
        context (obj): Used to run specific commands
        command (str): Command string to append to the "docker-compose ..." command, such as "build", "up", etc.
        **kwargs: Passed through to the context.run() call.
    """
    build_env = {
        "NAUTOBOT_VER": context.nautobot_chatops.nautobot_ver,
        "PYTHON_VER": context.nautobot_chatops.python_ver,
    }
    compose_command = f'docker-compose --project-name {context.nautobot_chatops.project_name} --project-directory "{context.nautobot_chatops.compose_dir}"'
    for compose_file in context.nautobot_chatops.compose_files:
        compose_file_path = os.path.join(context.nautobot_chatops.compose_dir, compose_file)
        compose_command += f' -f "{compose_file_path}"'
    compose_command += f" {command}"
    print(f'Running docker-compose command "{command}"')
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
            compose_command = f"run --entrypoint '{command}' nautobot"

        docker_compose(context, compose_command, pty=True)

# ------------------------------------------------------------------------------
# BUILD
# ------------------------------------------------------------------------------
@task
def build(context, nautobot_ver=NAUTOBOT_VER, python_ver=PYTHON_VER):
    """Build all docker images.

    Args:
        context (obj): Used to run specific commands
        nautobot_ver (str): Nautobot version to use to build the container
        python_ver (str): Will use the Python version docker image to build from
    """
    DEFAULT_ENV[NAUTOBOT_VER] = nautobot_ver
    DEFAULT_ENV[PYTHON_VER] = python_ver

    context.run(
        f"{COMPOSE_COMMAND} build",
        env=DEFAULT_ENV,
    )


# ------------------------------------------------------------------------------
# START / STOP / DEBUG
# ------------------------------------------------------------------------------
@task
def debug(context, nautobot_ver=NAUTOBOT_VER, python_ver=PYTHON_VER):
    """Start Nautobot and its dependencies in debug mode.

    Args:
        context (obj): Used to run specific commands
        nautobot_ver (str): Nautobot version to use to build the container
        python_ver (str): Will use the Python version docker image to build from
    """
    DEFAULT_ENV[NAUTOBOT_VER] = nautobot_ver
    DEFAULT_ENV[PYTHON_VER] = python_ver

    print("Starting Nautobot .. ")
    context.run(
        f"{COMPOSE_COMMAND} up",
        env=DEFAULT_ENV,
    )


@task
def start(context, nautobot_ver=NAUTOBOT_VER, python_ver=PYTHON_VER):
    """Start Nautobot and its dependencies in detached mode.

    Args:
        context (obj): Used to run specific commands
        nautobot_ver (str): Nautobot version to use to build the container
        python_ver (str): Will use the Python version docker image to build from
    """
    DEFAULT_ENV[NAUTOBOT_VER] = nautobot_ver
    DEFAULT_ENV[PYTHON_VER] = python_ver

    print("Starting Nautobot in detached mode.. ")
    context.run(
        f"{COMPOSE_COMMAND} up -d",
        env=DEFAULT_ENV,
    )


@task
def stop(context, nautobot_ver=NAUTOBOT_VER, python_ver=PYTHON_VER):
    """Stop Nautobot and its dependencies.

    Args:
        context (obj): Used to run specific commands
        nautobot_ver (str): Nautobot version to use to build the container
        python_ver (str): Will use the Python version docker image to build from
    """
    DEFAULT_ENV[NAUTOBOT_VER] = nautobot_ver
    DEFAULT_ENV[PYTHON_VER] = python_ver

    print("Stopping Nautobot .. ")
    context.run(
        f"{COMPOSE_COMMAND} down",
        env=DEFAULT_ENV,
    )


@task
def destroy(context, nautobot_ver=NAUTOBOT_VER, python_ver=PYTHON_VER):
    """Destroy all containers and volumes.

    Args:
        context (obj): Used to run specific commands
        nautobot_ver (str): Nautobot version to use to build the container
        python_ver (str): Will use the Python version docker image to build from
    """
    DEFAULT_ENV[NAUTOBOT_VER] = nautobot_ver
    DEFAULT_ENV[PYTHON_VER] = python_ver

    context.run(
        f"{COMPOSE_COMMAND} down",
        env=DEFAULT_ENV,
    )
    context.run(
        f"docker volume rm -f {BUILD_NAME}_pgdata_nautobot_golden_config",
        env=DEFAULT_ENV,
    )


# ------------------------------------------------------------------------------
# ACTIONS
# ------------------------------------------------------------------------------
@task
def nbshell(context, nautobot_ver=NAUTOBOT_VER, python_ver=PYTHON_VER):
    """Launch a nbshell session.

    Args:
        context (obj): Used to run specific commands
        nautobot_ver (str): Nautobot version to use to build the container
        python_ver (str): Will use the Python version docker image to build from
    """
    DEFAULT_ENV[NAUTOBOT_VER] = nautobot_ver
    DEFAULT_ENV[PYTHON_VER] = python_ver

    context.run(
        f"{COMPOSE_COMMAND} run nautobot nautobot-server nbshell",
        env=DEFAULT_ENV,
        pty=True,
    )


@task
def cli(context, nautobot_ver=NAUTOBOT_VER, python_ver=PYTHON_VER):
    """Launch a bash shell inside the running Nautobot container.

    Args:
        context (obj): Used to run specific commands
        nautobot_ver (str): Nautobot version to use to build the container
        python_ver (str): Will use the Python version docker image to build from
    """
    DEFAULT_ENV[NAUTOBOT_VER] = nautobot_ver
    DEFAULT_ENV[PYTHON_VER] = python_ver

    context.run(
        f"{COMPOSE_COMMAND} run nautobot bash",
        env=DEFAULT_ENV,
        pty=True,
    )


@task
def create_user(context, user="admin", nautobot_ver=NAUTOBOT_VER, python_ver=PYTHON_VER):
    """Create a new user in django (default: admin), will prompt for password.

    Args:
        context (obj): Used to run specific commands
        user (str): name of the superuser to create
        nautobot_ver (str): Nautobot version to use to build the container
        python_ver (str): Will use the Python version docker image to build from
    """
    DEFAULT_ENV[NAUTOBOT_VER] = nautobot_ver
    DEFAULT_ENV[PYTHON_VER] = python_ver

    context.run(
        f"{COMPOSE_COMMAND} run nautobot nautobot-server createsuperuser --username {user}",
        env=DEFAULT_ENV,
        pty=True,
    )


@task
def makemigrations(context, name="", nautobot_ver=NAUTOBOT_VER, python_ver=PYTHON_VER):
    """Run Make Migration in Django.

    Args:
        context (obj): Used to run specific commands
        name (str): Name of the migration to be created
        nautobot_ver (str): Nautobot version to use to build the container
        python_ver (str): Will use the Python version docker image to build from
    """
    DEFAULT_ENV[NAUTOBOT_VER] = nautobot_ver
    DEFAULT_ENV[PYTHON_VER] = python_ver

    context.run(
        f"{COMPOSE_COMMAND} up -d postgres",
        env=DEFAULT_ENV,
    )

    if name:
        context.run(
            f"{COMPOSE_COMMAND} run nautobot nautobot-server makemigrations nautobot_golden_config --name {name}",
            env=DEFAULT_ENV,
        )
    else:
        context.run(
            f"{COMPOSE_COMMAND} run nautobot nautobot-server makemigrations nautobot_golden_config",
            env=DEFAULT_ENV,
        )

    context.run(
        f"{COMPOSE_COMMAND} down",
        env=DEFAULT_ENV,
    )


# ------------------------------------------------------------------------------
# TESTS / LINTING
# ------------------------------------------------------------------------------
@task
def unittest(context, nautobot_ver=NAUTOBOT_VER, python_ver=PYTHON_VER):
    """Run Django unit tests for the plugin.

    Args:
        context (obj): Used to run specific commands
        nautobot_ver (str): Nautobot version to use to build the container
        python_ver (str): Will use the Python version docker image to build from
    """
    DEFAULT_ENV[NAUTOBOT_VER] = nautobot_ver
    DEFAULT_ENV[PYTHON_VER] = python_ver

    docker = f"{COMPOSE_COMMAND} run --entrypoint='' nautobot "
    context.run(
        f'{docker} sh -c "nautobot-server test nautobot_golden_config"',
        env=DEFAULT_ENV,
        pty=True,
    )


@task
def pylint(context, nautobot_ver=NAUTOBOT_VER, python_ver=PYTHON_VER):
    """Run pylint code analysis.

    Args:
        context (obj): Used to run specific commands
        nautobot_ver (str): Nautobot version to use to build the container
        python_ver (str): Will use the Python version docker image to build from
    """
    DEFAULT_ENV[NAUTOBOT_VER] = nautobot_ver
    DEFAULT_ENV[PYTHON_VER] = python_ver

    docker = f"{COMPOSE_COMMAND} run --entrypoint='' nautobot "
    # We exclude the /migrations/ directory since it is autogenerated code
    context.run(
        f"{docker} sh -c \"cd /source && find . -name '*.py' -not -path '*/migrations/*' | "
        'PYTHONPATH=/source/development DJANGO_SETTINGS_MODULE=nautobot_config xargs pylint"',
        env=DEFAULT_ENV,
        pty=True,
    )


@task
def black(context):
    """Run black to check that Python files adhere to its style standards.

    Args:
        context (obj): Used to run specific commands
    """

    command = f"black --check --diff ."
    run_command(context, command)
    return

    DEFAULT_ENV[NAUTOBOT_VER] = nautobot_ver
    DEFAULT_ENV[PYTHON_VER] = python_ver

    docker = f"{COMPOSE_COMMAND} run --entrypoint='' nautobot "
    context.run(
        f'{docker} sh -c "cd /source && black --check --diff ."',
        env=DEFAULT_ENV,
        pty=True,
    )


@task
def pydocstyle(context, nautobot_ver=NAUTOBOT_VER, python_ver=PYTHON_VER):
    """Run pydocstyle to validate docstring formatting adheres to NTC defined standards.

    Args:
        context (obj): Used to run specific commands
        nautobot_ver (str): Nautobot version to use to build the container
        python_ver (str): Will use the Python version docker image to build from
    """
    DEFAULT_ENV[NAUTOBOT_VER] = nautobot_ver
    DEFAULT_ENV[PYTHON_VER] = python_ver

    docker = f"{COMPOSE_COMMAND} run --entrypoint='' nautobot "
    # We exclude the /migrations/ directory since it is autogenerated code
    context.run(
        f"{docker} sh -c \"cd /source && find . -name '*.py' -not -path '*/migrations/*' | xargs pydocstyle\"",
        env=DEFAULT_ENV,
        pty=True,
    )


@task
def bandit(context, nautobot_ver=NAUTOBOT_VER, python_ver=PYTHON_VER):
    """Run bandit to validate basic static code security analysis.

    Args:
        context (obj): Used to run specific commands
        nautobot_ver (str): Nautobot version to use to build the container
        python_ver (str): Will use the Python version docker image to build from
    """
    DEFAULT_ENV[NAUTOBOT_VER] = nautobot_ver
    DEFAULT_ENV[PYTHON_VER] = python_ver

    docker = f"{COMPOSE_COMMAND} run --entrypoint='' nautobot "
    context.run(
        f'{docker} sh -c "cd /source && bandit --recursive ./ --configfile .bandit.yml"',
        env=DEFAULT_ENV,
        pty=True,
    )


@task
def tests(context, nautobot_ver=NAUTOBOT_VER, python_ver=PYTHON_VER):
    """Run all tests for this plugin.

    Args:
        context (obj): Used to run specific commands
        nautobot_ver (str): Nautobot version to use to build the container
        python_ver (str): Will use the Python version docker image to build from
    """
    DEFAULT_ENV[NAUTOBOT_VER] = nautobot_ver
    DEFAULT_ENV[PYTHON_VER] = python_ver

    # Sorted loosely from fastest to slowest
    print("Running black...")
    black(context, nautobot_ver=nautobot_ver, python_ver=python_ver)
    print("Running bandit...")
    bandit(context, nautobot_ver=nautobot_ver, python_ver=python_ver)
    print("Running pydocstyle...")
    pydocstyle(context, nautobot_ver=nautobot_ver, python_ver=python_ver)
    print("Running pylint...")
    pylint(context, nautobot_ver=nautobot_ver, python_ver=python_ver)
    print("Running unit tests...")
    unittest(context, nautobot_ver=nautobot_ver, python_ver=python_ver)

    print("All tests have passed!")
