# Contributing to the App

The project is packaged with a light development environment based on `docker-compose` to help with the local development of the project and to run tests within TravisCI.

The project is following Network to Code software development guidelines and are leveraging the following:
- Black, Pylint, Bandit, flake8, and pydocstyle for Python linting and formatting.
- Django unit test to ensure the plugin is working properly.

## Branching Policy

The branching policy includes the following tenets:

- The develop branch is the branch of the next major and minor paired version planned.
- The `stable-<major>.<minor>` branch is the branch of the latest version within that major/minor version.
- The `stable-<major>.<minor>` branch will have all of the latest bug fixes and security patches, and may or may not represent the released version.
- PRs intended to add new features should be sourced from the develop branch.
- PRs intended to add new features that break backward compatability should be discussed before a PR is created.
- PRs intended to address bug fixes and security patches should be sourced from `stable-<major>.<minor>`.

Nautobot Golden Config will observe semantic versioning, as of 1.0. This may result in an quick turn around in minor versions to keep
pace with an ever growing feature set.

## Release Policy

Nautobot Golden Config has currently no intended scheduled release schedule, and will release new feature in minor versions.

When a new release of any kind (e.g. from develop to main, or a release of a `stable-<major>.<minor>`) is created the following should happen.
- A release PR is created with:
  - Update to the CHANGELOG.md file to reflect the changes.
  - Change the version from `<major>.<minor>.<patch>-beta` to `<major>.<minor>.<patch>` in pyproject.toml.
  - Set the PR to the proper branch, e.g. either `main` or `stable-<major>.<minor>`.
- Ensure the tests for the PR pass.
- Merge the PR.
- Create a new tag:
  - The tag should be in the form of `v<major>.<minor>.<patch>`.
  - The title should be in the form of `v<major>.<minor>.<patch>`.
  - The description should be the changes that were added to the CHANGELOG.md document.
- If merged into main, then push from main to develop, in order to retain the merge commit created when the PR was merged
- If the is a new `<major>.<minor>`, create a `stable-<major>.<minor>` branch and push that to the repo.
- A post release PR is created with.
  - Change the version from `<major>.<minor>.<patch>` to `<major>.<minor>.<patch + 1>-beta` in both pyproject.toml and `nautobot.__init__.__version__`.
  - Set the PR to the proper branch, e.g. either `develop` or `stable-<major>.<minor>`.
  - Once tests pass, merge. 


### Development Environment

The development environment can be used in 2 ways. First, with a local poetry environment if you wish to develop outside of Docker with the caveat of using external services provided by Docker for PostgresQL and Redis. Second, all services are spun up using Docker and a local mount so you can develop locally, but Nautobot is spun up within the Docker container.

Below is a quick start guide if you're already familiar with the development environment provided, but if you're not familiar, please read the [Getting Started Guide](GETTING_STARTED.md).

#### Invoke

The [PyInvoke](http://www.pyinvoke.org/) library is used to provide some helper commands based on the environment. There are a few configuration parameters which can be passed to PyInvoke to override the default configuration:

- `nautobot_ver`: the version of Nautobot to use as a base for any built docker containers (default: latest)
- `project_name`: the default docker compose project name (default: nautobot_golden_config)
- `python_ver`: the version of Python to use as a base for any built docker containers (default: 3.8)
- `local`: a boolean flag indicating if invoke tasks should be run on the host or inside the docker containers (default: False, commands will be run in docker containers)
- `compose_dir`: the full path to a directory containing the project compose files
- `compose_files`: a list of compose files applied in order (see [Multiple Compose files](https://docs.docker.com/compose/extends/#multiple-compose-files) for more information)

Using **PyInvoke** these configuration options can be overridden using [several methods](http://docs.pyinvoke.org/en/stable/concepts/configuration.html). Perhaps the simplest is simply setting an environment variable `INVOKE_NAUTOBOT_GOLDEN_CONFIG_VARIABLE_NAME` where `VARIABLE_NAME` is the variable you are trying to override. The only exception is `compose_files`, because it is a list it must be overridden in a yaml file. There is an example `invoke.yml` (`invoke.example.yml`) in this directory which can be used as a starting point.

#### Local Poetry Development Environment

- Create an `invoke.yml` file with the following contents at the root of the repo and edit as necessary

```yaml
---
nautobot_golden_config:
  local: true
  compose_files:
    - "docker-compose.requirements.yml"
```

3. Run the following commands:

```shell
poetry shell
poetry install --extras nautobot
export $(cat development/dev.env | xargs)
export $(cat development/creds.env | xargs)
invoke start && sleep 5
nautobot-server migrate
```

> If you want to develop on the latest develop branch of Nautobot, run the following command: `poetry add --optional git+https://github.com/nautobot/nautobot@develop`. After the `@` symbol must match either a branch or a tag.

4. You can now run nautobot-server commands as you would from the [Nautobot documentation](https://nautobot.readthedocs.io/en/latest/) for example to start the development server:

```shell
nautobot-server runserver 0.0.0.0:8080 --insecure
```

Nautobot server can now be accessed at [http://localhost:8080](http://localhost:8080).

It is typically recommended to launch the Nautobot **runserver** command in a separate shell so you can keep developing and manage the webserver separately.

#### Docker Development Environment

This project is managed by [Python Poetry](https://python-poetry.org/) and has a few requirements to setup your development environment:

1. Install Poetry, see the [Poetry Documentation](https://python-poetry.org/docs/#installation) for your operating system.
2. Install Docker, see the [Docker documentation](https://docs.docker.com/get-docker/) for your operating system.

Once you have Poetry and Docker installed you can run the following commands to install all other development dependencies in an isolated python virtual environment:

```shell
poetry shell
poetry install
invoke start
```

Nautobot server can now be accessed at [http://localhost:8080](http://localhost:8080).

To either stop or destroy the development environment use the following options.

- **invoke stop** - Stop the containers, but keep all underlying systems intact
- **invoke destroy** - Stop and remove all containers, volumes, etc. (This results in data loss due to the volume being deleted)

### CLI Helper Commands


The project features a CLI helper based on [invoke](http://www.pyinvoke.org/) to help setup the development environment. The commands are listed below in 3 categories:
- `dev environment`
- `utility`
- `testing`. 

Each command can be executed with `invoke <command>`. All commands support the arguments `--nautobot-ver` and `--python-ver` if you want to manually define the version of Python and Nautobot to use. Each command also has its own help `invoke <command> --help`

> Note: to run the mysql (mariadb) development environment, set the environment variable as such `export NAUTOBOT_USE_MYSQL=1`.


### Local Development Environment

```
  build            Build all docker images.
  debug            Start Nautobot and its dependencies in debug mode.
  destroy          Destroy all containers and volumes.
  restart          Restart Nautobot and its dependencies in detached mode.
  start            Start Nautobot and its dependencies in detached mode.
  stop             Stop Nautobot and its dependencies.
```

### Utility 

```
  cli              Launch a bash shell inside the running Nautobot container.
  create-user      Create a new user in django (default: admin), will prompt for password.
  makemigrations   Run Make Migration in Django.
  nbshell          Launch a nbshell session.
```

### Testing 

```
  bandit           Run bandit to validate basic static code security analysis.
  black            Run black to check that Python files adhere to its style standards.
  flake8           Run flake8 to check that Python files adhere to its style standards.
  pydocstyle       Run pydocstyle to validate docstring formatting adheres to NTC defined standards.
  pylint           Run pylint code analysis.
  tests            Run all tests for this plugin.
  unittest         Run Django unit tests for the plugin.
```
