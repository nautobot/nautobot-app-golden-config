"""Tasks for use with Invoke."""

import os
from distutils.util import strtobool
from invoke import Collection, task as invoke_task


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


COMPOSE_FILES = ["docker-compose.yml", "../docker-compose.override.yml"]
if os.getenv("NAUTOBOT_USE_MYSQL"):
    COMPOSE_FILES.append("docker-compose.mysql.yml")

namespace = Collection("nautobot_golden_config")
namespace.configure(
    {
        "nautobot_golden_config": {
            "nautobot_ver": "1.2.1",
            "project_name": "nautobot_golden_config",
            "python_ver": "3.7",
            "local": False,
            "compose_dir": os.path.join(os.path.dirname(__file__), "development"),
            "compose_files": COMPOSE_FILES,
        }
    }
)


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
    """Helper function for running a specific docker-compose command with all appropriate parameters and environment.

    Args:
        context (obj): Used to run specific commands
        command (str): Command string to append to the "docker-compose ..." command, such as "build", "up", etc.
        **kwargs: Passed through to the context.run() call.
    """
    build_env = {
        "NAUTOBOT_VER": context.nautobot_golden_config.nautobot_ver,
        "PYTHON_VER": context.nautobot_golden_config.python_ver,
    }
    compose_command = f'docker-compose --project-name {context.nautobot_golden_config.project_name} --project-directory "{context.nautobot_golden_config.compose_dir}"'
    for compose_file in context.nautobot_golden_config.compose_files:
        compose_file_path = os.path.join(context.nautobot_golden_config.compose_dir, compose_file)
        if os.path.isfile(compose_file_path):
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
@task(
    help={
        "force_rm": "Always remove intermediate containers",
        "cache": "Whether to use Docker's cache when building the image (defaults to enabled)",
    }
)
def build(context, force_rm=False, cache=True):
    """Build all docker images.

    Args:
        context (obj): Used to run specific commands
    """
    command = "build"

    if not cache:
        command += " --no-cache"
    if force_rm:
        command += " --force-rm"

    print(f"Building Nautobot with Python {context.nautobot_golden_config.python_ver}...")
    docker_compose(context, command)


# ------------------------------------------------------------------------------
# START / STOP / DEBUG
# ------------------------------------------------------------------------------
@task
def debug(context):
    """Start Nautobot and its dependencies in debug mode.

    Args:
        context (obj): Used to run specific commands
    """
    print("Starting Nautobot in debug mode...")
    docker_compose(context, "up")


@task
def start(context):
    """Start Nautobot and its dependencies in detached mode.

    Args:
        context (obj): Used to run specific commands
    """
    print("Starting Nautobot in detached mode.. ")
    docker_compose(context, "up --detach")


@task
def stop(context):
    """Stop Nautobot and its dependencies.

    Args:
        context (obj): Used to run specific commands
    """
    print("Stopping Nautobot...")
    docker_compose(context, "down")


@task
def restart(context):
    """Gracefully restart all containers."""
    print("Restarting Nautobot...")
    docker_compose(context, "restart")


@task
def destroy(context):
    """Destroy all containers and volumes.

    Args:
        context (obj): Used to run specific commands
    """
    print("Destroying Nautobot...")
    docker_compose(context, "down --volumes")


# ------------------------------------------------------------------------------
# ACTIONS
# ------------------------------------------------------------------------------
@task
def nbshell(context):
    """Launch a nbshell session.

    Args:
        context (obj): Used to run specific commands
    """
    command = "nautobot-server nbshell"
    run_command(context, command)


@task
def cli(context):
    """Launch a bash shell inside the running Nautobot container.

    Args:
        context (obj): Used to run specific commands
    """
    run_command(context, "bash")


@task(
    help={
        "user": "name of the superuser to create (default: admin)",
    }
)
def create_user(context, user="admin"):
    """Create a new user in django (default: admin), will prompt for password.

    Args:
        context (obj): Used to run specific commands
        user (str): name of the superuser to create
    """
    command = f"nautobot-server createsuperuser --username {user}"
    run_command(context, command)


@task(
    help={
        "name": "name of the migration to be created; if unspecified, will autogenerate a name",
    }
)
def makemigrations(context, name=""):
    """Run Make Migration in Django.

    Args:
        context (obj): Used to run specific commands
        name (str): Name of the migration to be created
    """
    command = "nautobot-server makemigrations nautobot_golden_config"

    if name:
        command += f" --name {name}"

    run_command(context, command)


# ------------------------------------------------------------------------------
# TESTS / LINTING
# ------------------------------------------------------------------------------
@task
def unittest(context, label="nautobot_golden_config"):
    """Run Django unit tests for the plugin.

    Args:
        context (obj): Used to run specific commands
        label (str): Specify a directory or module to test instead of running all Nautobot Golden Config tests.
    """
    command = f"nautobot-server test {label}"
    run_command(context, command)


@task
def pylint(context):
    """Run pylint code analysis.

    Args:
        context (obj): Used to run specific commands
    """
    command = 'pylint --init-hook "import nautobot; nautobot.setup()" --rcfile pyproject.toml nautobot_golden_config'
    run_command(context, command)


@task
def black(context):
    """Run black to check that Python files adhere to its style standards.

    Args:
        context (obj): Used to run specific commands
    """
    command = "black --check --diff ."
    run_command(context, command)


@task
def pydocstyle(context):
    """Run pydocstyle to validate docstring formatting adheres to NTC defined standards.

    Args:
        context (obj): Used to run specific commands
    """
    command = "pydocstyle --config=.pydocstyle.ini"
    run_command(context, command)


@task
def bandit(context):
    """Run bandit to validate basic static code security analysis.

    Args:
        context (obj): Used to run specific commands
    """
    command = "bandit --recursive . --configfile .bandit.yml"
    run_command(context, command)


@task
def yamllint(context):
    """Run yamllint to validate formating adheres to NTC defined YAML standards.

    Args:
        context (obj): Used to run specific commands
    """
    command = "yamllint . --format standard"
    run_command(context, command)


@task
def flake8(context):
    """Check for PEP8 compliance and other style issues."""
    command = "flake8 ."
    run_command(context, command)


@task
def tests(context):
    """Run all tests for this plugin.

    Args:
        context (obj): Used to run specific commands
    """
    if not is_truthy(context.nautobot_golden_config.local):
        print("Starting Docker Containers...")
        start(context)
    # Sorted loosely from fastest to slowest
    print("Running black...")
    black(context)
    print("Running bandit...")
    bandit(context)
    print("Running pydocstyle...")
    pydocstyle(context)
    print("Running yamllint...")
    yamllint(context)
    print("Running flake8...")
    flake8(context)
    print("Running pylint...")
    pylint(context)
    print("Running unit tests...")
    unittest(context)

    print("All tests have passed!")
