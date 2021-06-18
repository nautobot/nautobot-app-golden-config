"""Tasks for use with Invoke."""

import os
import sys
import requests
from invoke import task

try:
    import toml
except ImportError:
    sys.exit("Please make sure to `pip install toml` or enable the Poetry shell and run `poetry install`.")

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

PYPROJECT_CONFIG = toml.load("pyproject.toml")
# Get project name from the toml file
PROJECT_NAME = PYPROJECT_CONFIG["tool"]["poetry"]["name"]
# Get current project version from the toml file
PROJECT_VERSION = PYPROJECT_CONFIG["tool"]["poetry"]["version"]

environment = DEFAULT_ENV
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
def black(context, nautobot_ver=NAUTOBOT_VER, python_ver=PYTHON_VER):
    """Run black to check that Python files adhere to its style standards.

    Args:
        context (obj): Used to run specific commands
        nautobot_ver (str): Nautobot version to use to build the container
        python_ver (str): Will use the Python version docker image to build from
    """
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


@task
def check_pypi_version(context, name=PROJECT_NAME, version=PROJECT_VERSION):
    """Verify if the version specified already exists on PyPI.

    Used mostly in CI/CD to make sure that the new version is merged to main.
    If version already exists, then function exits with non-zero return code,
    else the function exits with zero return code.

    Args:
        context (obj): Used to run specific commands
        name (str): The name of the project
        version (str): The version of the project
    """
    # Running the following from context to pass pylint:
    # context must be the first argument in invoke
    context.run(f"echo Verifying the version {version} on PyPI.")

    url = f"https://pypi.org/pypi/{name}/json"
    response = requests.get(url)
    data = response.json()
    if version in data.get("releases", {}).keys():
        print(f"The version {version} already exists.")
        print("Bump the version. Run the command: poetry version.")
        sys.exit(1)
    print(f"The version {version} does not exist on PyPI.")
    print("The version can be released.")
    sys.exit(0)
