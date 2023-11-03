# Building Your Development Environment

## Quickstart Guide

The development environment can be used in two ways:

1. **(Recommended)** All services, including Nautobot, are spun up using Docker containers and a volume mount so you can develop locally.
2. With a local Poetry environment if you wish to develop outside of Docker, with the caveat of using external services provided by Docker for the database (PostgreSQL by default, MySQL optionally) and Redis services.

This is a quick reference guide if you're already familiar with the development environment provided, which you can read more about later in this document.

### Invoke

The [Invoke](http://www.pyinvoke.org/) library is used to provide some helper commands based on the environment. There are a few configuration parameters which can be passed to Invoke to override the default configuration:

- `nautobot_ver`: the version of Nautobot to use as a base for any built docker containers (default: 2.0.0)
- `project_name`: the default docker compose project name (default: `nautobot-golden-config`)
- `python_ver`: the version of Python to use as a base for any built docker containers (default: 3.11)
- `local`: a boolean flag indicating if invoke tasks should be run on the host or inside the docker containers (default: False, commands will be run in docker containers)
- `compose_dir`: the full path to a directory containing the project compose files
- `compose_files`: a list of compose files applied in order (see [Multiple Compose files](https://docs.docker.com/compose/extends/#multiple-compose-files) for more information)

Using **Invoke** these configuration options can be overridden using [several methods](https://docs.pyinvoke.org/en/stable/concepts/configuration.html). Perhaps the simplest is setting an environment variable `INVOKE_NAUTOBOT_GOLDEN_CONFIG_VARIABLE_NAME` where `VARIABLE_NAME` is the variable you are trying to override. The only exception is `compose_files`, because it is a list it must be overridden in a YAML file. There is an example `invoke.yml` (`invoke.example.yml`) in this directory which can be used as a starting point.

### Docker Development Environment

!!! tip
    This is the recommended option for development.

This project is managed by [Python Poetry](https://python-poetry.org/) and has a few requirements to setup your development environment:

1. Install Poetry, see the [Poetry Documentation](https://python-poetry.org/docs/#installation) for your operating system.
2. Install Docker, see the [Docker documentation](https://docs.docker.com/get-docker/) for your operating system.

Once you have Poetry and Docker installed you can run the following commands (in the root of the repository) to install all other development dependencies in an isolated Python virtual environment:

```shell
poetry shell
poetry install
cp development/creds.example.env development/creds.env
invoke build
invoke start
```

The Nautobot server can now be accessed at [http://localhost:8080](http://localhost:8080) and the live documentation at [http://localhost:8001](http://localhost:8001).

To either stop or destroy the development environment use the following options.

- **invoke stop** - Stop the containers, but keep all underlying systems intact
- **invoke destroy** - Stop and remove all containers, volumes, etc. (This results in data loss due to the volume being deleted)

### Local Poetry Development Environment

- Create an `invoke.yml` file with the following contents at the root of the repo and edit as necessary

```yaml
---
nautobot_golden_config:
  local: true
```

Run the following commands:

```shell
poetry shell
poetry install --extras nautobot
export $(cat development/development.env | xargs)
export $(cat development/creds.env | xargs)
invoke start && sleep 5
nautobot-server migrate
```

!!! note
    If you want to develop on the latest develop branch of Nautobot, run the following command: `poetry add --optional git+https://github.com/nautobot/nautobot@develop`. After the `@` symbol must match either a branch or a tag.

You can now run `nautobot-server` commands as you would from the [Nautobot documentation](https://nautobot.readthedocs.io/en/latest/) for example to start the development server:

```shell
nautobot-server runserver 0.0.0.0:8080 --insecure
```

Nautobot server can now be accessed at [http://localhost:8080](http://localhost:8080).

It is typically recommended to launch the Nautobot **runserver** command in a separate shell so you can keep developing and manage the webserver separately.

### Updating the Documentation

Documentation dependencies are pinned to exact versions to ensure consistent results. For the development environment, they are defined in the `pyproject.toml` file.

If you need to update any of the documentation dependencies to a newer version, make sure you copy the exact same versions pinned in `pyproject.toml` to the `docs/requirements.txt` file as well. The latter is used in the automated build pipeline on ReadTheDocs to build the live version of the documentation.

### CLI Helper Commands

The project features a CLI helper based on [Invoke](https://www.pyinvoke.org/) to help setup the development environment. The commands are listed below in 3 categories:

- `dev environment`
- `utility`
- `testing`

Each command can be executed with `invoke <command>`. All commands support the arguments `--nautobot-ver` and `--python-ver` if you want to manually define the version of Python and Nautobot to use. Each command also has its own help `invoke <command> --help`

#### Local Development Environment

```
  build            Build all docker images.
  debug            Start Nautobot and its dependencies in debug mode.
  destroy          Destroy all containers and volumes.
  restart          Restart Nautobot and its dependencies in detached mode.
  start            Start Nautobot and its dependencies in detached mode.
  stop             Stop Nautobot and its dependencies.
```

#### Utility

```
  cli              Launch a bash shell inside the running Nautobot container.
  create-user      Create a new user in django (default: admin), will prompt for password.
  makemigrations   Run Make Migration in Django.
  nbshell          Launch a nbshell session.
```

#### Testing

```
  bandit           Run bandit to validate basic static code security analysis.
  black            Run black to check that Python files adhere to its style standards.
  flake8           Run flake8 to check that Python files adhere to its style standards.
  pydocstyle       Run pydocstyle to validate docstring formatting adheres to NTC defined standards.
  pylint           Run pylint code analysis.
  tests            Run all tests for this plugin.
  unittest         Run Django unit tests for the plugin.
```

## Project Overview

This project provides the ability to develop and manage the Nautobot server locally (with supporting services being *Dockerized*) or by using only Docker containers to manage Nautobot. The main difference between the two environments is the ability to debug and use **pdb** when developing locally. Debugging with **pdb** within the Docker container is more complicated, but can still be accomplished by either entering into the container (via `docker exec`) or attaching your IDE to the container and running the Nautobot service manually within the container.

The upside to having the Nautobot service handled by Docker rather than locally is that you do not have to manage the Nautobot server. The [Docker logs](#docker-logs) provide the majority of the information you will need to help troubleshoot, while getting started quickly and not requiring you to perform several manual steps and remembering to have the Nautobot server running in a separate terminal while you develop.

!!! note
	The local environment still uses Docker containers for the supporting services (Postgres, Redis, and RQ Worker), but the Nautobot server is handled locally by you, the developer.

Follow the directions below for the specific development environment that you choose.

## Poetry

Poetry is used in lieu of the "virtualenv" commands and is leveraged in both environments. The virtual environment will provide all of the Python packages required to manage the development environment such as **Invoke**. See the [Local Development Environment](#local-poetry-development-environment) section to see how to install Nautobot if you're going to be developing locally (i.e. not using the Docker container).

The `pyproject.toml` file outlines all of the relevant dependencies for the project:

- `tool.poetry.dependencies` - the main list of dependencies.
- `tool.poetry.group.dev.dependencies` - development dependencies, to facilitate linting, testing, and documentation building.

The `poetry shell` command is used to create and enable a virtual environment managed by Poetry, so all commands ran going forward are executed within the virtual environment. This is similar to running the `source venv/bin/activate` command with virtualenvs. To install project dependencies in the virtual environment, you should run `poetry install` - this will install **both** project and development dependencies.

For more details about Poetry and its commands please check out its [online documentation](https://python-poetry.org/docs/).

## Full Docker Development Environment

This project is set up with a number of **Invoke** tasks consumed as simple CLI commands to get developing fast. You'll use a few `invoke` commands to get your environment up and running.

### Copy the credentials file for Nautobot

First, you need to create the `development/creds.env` file - it stores a bunch of private information such as passwords and tokens for your local Nautobot install. You can make a copy of the `development/creds.example.env` and modify it to suit you.

```shell
cp development/creds.example.env development/creds.env
```

### Invoke - Building the Docker Image

The first thing you need to do is build the necessary Docker image for Nautobot that installs the specific `nautobot_ver`. The image is used for Nautobot and the Celery worker service used by Docker Compose.

```bash
➜ invoke build
... <omitted for brevity>
#14 exporting to image
#14 sha256:e8c613e07b0b7ff33893b694f7759a10d42e180f2b4dc349fb57dc6b71dcab00
#14 exporting layers
#14 exporting layers 1.2s done
#14 writing image sha256:2d524bc1665327faa0d34001b0a9d2ccf450612bf8feeb969312e96a2d3e3503 done
#14 naming to docker.io/nautobot-golden-config/nautobot:2.0.0-py3.11 done
```

### Invoke - Starting the Development Environment

Next, you need to start up your Docker containers.

```bash
➜ invoke start
Starting Nautobot in detached mode...
Running docker-compose command "up --detach"
Creating network "nautobot_golden_config_default" with the default driver
Creating volume "nautobot_golden_config_postgres_data" with default driver
Creating nautobot_golden_config_redis_1 ...
Creating nautobot_golden_config_docs_1  ...
Creating nautobot_golden_config_postgres_1 ...
Creating nautobot_golden_config_postgres_1 ... done
Creating nautobot_golden_config_redis_1    ... done
Creating nautobot_golden_config_nautobot_1 ...
Creating nautobot_golden_config_docs_1     ... done
Creating nautobot_golden_config_nautobot_1 ... done
Creating nautobot_golden_config_worker_1   ...
Creating nautobot_golden_config_worker_1   ... done
Docker Compose is now in the Docker CLI, try `docker compose up`
```

This will start all of the Docker containers used for hosting Nautobot. You should see the following containers running after `invoke start` is finished.

```bash
➜ docker ps
****CONTAINER ID   IMAGE                            COMMAND                  CREATED          STATUS          PORTS                                       NAMES
ee90fbfabd77   nautobot-golden-config/nautobot:2.0.0-py3.11  "nautobot-server rqw…"   16 seconds ago   Up 13 seconds                                               nautobot_golden_config_worker_1
b8adb781d013   nautobot-golden-config/nautobot:2.0.0-py3.11  "/docker-entrypoint.…"   20 seconds ago   Up 15 seconds   0.0.0.0:8080->8080/tcp, :::8080->8080/tcp   nautobot_golden_config_nautobot_1
d64ebd60675d   nautobot-golden-config/nautobot:2.0.0-py3.11  "mkdocs serve -v -a …"   25 seconds ago   Up 18 seconds   0.0.0.0:8001->8080/tcp, :::8001->8080/tcp   nautobot_golden_config_docs_1
e72d63129b36   postgres:13-alpine               "docker-entrypoint.s…"   25 seconds ago   Up 19 seconds   0.0.0.0:5432->5432/tcp, :::5432->5432/tcp   nautobot_golden_config_postgres_1
96c6ff66997c   redis:6-alpine                   "docker-entrypoint.s…"   25 seconds ago   Up 21 seconds   0.0.0.0:6379->6379/tcp, :::6379->6379/tcp   nautobot_golden_config_redis_1
```

Once the containers are fully up, you should be able to open up a web browser, and view:

- The Nautobot homepage at [http://localhost:8080](http://localhost:8080)
- A live version of the documentation at [http://localhost:8001](http://localhost:8001)

!!! note
	Sometimes the containers take a minute to fully spin up. If the page doesn't load right away, wait a minute and try again.

### Invoke - Creating a Superuser

The Nautobot development image will automatically provision a super user when specifying the following variables within `creds.env` which is the default when copying `creds.example.env` to `creds.env`.

- `NAUTOBOT_CREATE_SUPERUSER=true`
- `NAUTOBOT_SUPERUSER_API_TOKEN=0123456789abcdef0123456789abcdef01234567`
- `NAUTOBOT_SUPERUSER_PASSWORD=admin`

!!! note
	The default username is **admin**, but can be overridden by specifying **NAUTOBOT_SUPERUSER_USERNAME**.

If you need to create additional superusers, run the follow commands.

```bash
➜ invoke createsuperuser
Running docker-compose command "ps --services --filter status=running"
Running docker-compose command "exec nautobot nautobot-server createsuperuser --username admin"
Error: That username is already taken.
Username: ntc
Email address: ntc@networktocode.com
Password:
Password (again):
Superuser created successfully.
```

### Invoke - Stopping the Development Environment

The last command to know for now is `invoke stop`.

```bash
➜ invoke stop
Stopping Nautobot...
Running docker-compose command "down"
Stopping nautobot_golden_config_worker_1   ...
Stopping nautobot_golden_config_nautobot_1 ...
Stopping nautobot_golden_config_docs_1     ...
Stopping nautobot_golden_config_redis_1    ...
Stopping nautobot_golden_config_postgres_1 ...
Stopping nautobot_golden_config_worker_1   ... done
Stopping nautobot_golden_config_nautobot_1 ... done
Stopping nautobot_golden_config_postgres_1 ... done
Stopping nautobot_golden_config_redis_1    ... done
Stopping nautobot_golden_config_docs_1     ... done
Removing nautobot_golden_config_worker_1   ...
Removing nautobot_golden_config_nautobot_1 ...
Removing nautobot_golden_config_docs_1     ...
Removing nautobot_golden_config_redis_1    ...
Removing nautobot_golden_config_postgres_1 ...
Removing nautobot_golden_config_postgres_1 ... done
Removing nautobot_golden_config_docs_1     ... done
Removing nautobot_golden_config_worker_1   ... done
Removing nautobot_golden_config_redis_1    ... done
Removing nautobot_golden_config_nautobot_1 ... done
Removing network nautobot_golden_config_default
```

This will safely shut down all of your running Docker containers for this project. When you are ready to spin containers back up, it is as simple as running `invoke start` again [as seen previously](#invoke-starting-the-development-environment).

!!! warning
	If you're wanting to reset the database and configuration settings, you can use the `invoke destroy` command, but **you will lose any data stored in those containers**, so make sure that is what you want to do.

### Real-Time Updates? How Cool!

Your environment should now be fully setup, all necessary Docker containers are created and running, and you're logged into Nautobot in your web browser. Now what?

Now you can start developing your plugin in the project folder!

The magic here is the root directory is mounted inside your Docker containers when built and ran, so **any** changes made to the files in here are directly updated to the Nautobot plugin code running in Docker. This means that as you modify the code in your plugin folder, the changes will be instantly updated in Nautobot.

!!! warning
	There are a few exceptions to this, as outlined in the section [To Rebuild or Not To Rebuild](#to-rebuild-or-not-to-rebuild).

The back-end Django process is setup to automatically reload itself (it only takes a couple of seconds) every time a file is updated (saved). So for example, if you were to update one of the files like `tables.py`, then save it, the changes will be visible right away in the web browser!

!!! note
	You may get connection refused while Django reloads, but it should be refreshed fairly quickly.

### Docker Logs

When trying to debug an issue, one helpful thing you can look at are the logs within the Docker containers.

```bash
➜ docker logs <name of container> -f
```

!!! note
	The `-f` tag will keep the logs open, and output them in realtime as they are generated.

!!! info
    Want to limit the log output even further? Use the `--tail <#>` command line argument in conjunction with `-f`.

So for example, our plugin is named `nautobot-golden-config`, the command would most likely be `docker logs nautobot_golden_config_nautobot_1 -f`. You can find the name of all running containers via `docker ps`.

If you want to view the logs specific to the worker container, simply use the name of that container instead.

## To Rebuild or Not to Rebuild

Most of the time, you will not need to rebuild your images. Simply running `invoke start` and `invoke stop` is enough to keep your environment going.

However there are a couple of instances when you will want to.

### Updating Environment Variables

To add environment variables to your containers, thus allowing Nautobot to use them, you will update/add them in the `development/development.env` file. However, doing so is considered updating the underlying container shell, instead of Django (which auto restarts itself on changes).

To get new environment variables to take effect, you will need stop any running images, rebuild the images, then restart them. This can easily be done with 3 commands:

```bash
➜ invoke stop
➜ invoke build
➜ invoke start
```

Once completed, the new/updated environment variables should now be live.

### Installing Additional Python Packages

If you want your plugin to leverage another available Nautobot plugin or another Python package, you can easily add them into your Docker environment.

```bash
➜ poetry shell
➜ poetry add <package_name>
```

Once the dependencies are resolved, stop the existing containers, rebuild the Docker image, and then start all containers again.

```bash
➜ invoke stop
➜ invoke build
➜ invoke start
```

### Installing Additional Nautobot Plugins

Let's say for example you want the new plugin you're creating to integrate into Slack. To do this, you will want to integrate into the existing Nautobot ChatOps Plugin.

```bash
➜ poetry shell
➜ poetry add nautobot-chatops
```

Once you activate the virtual environment via Poetry, you then tell Poetry to install the new plugin.

Before you continue, you'll need to update the file `development/nautobot_config.py` accordingly with the name of the new plugin under `PLUGINS` and any relevant settings as necessary for the plugin under `PLUGINS_CONFIG`. Since you're modifying the underlying OS (not just Django files), you need to rebuild the image. This is a similar process to updating environment variables, which was explained earlier.

```bash
➜ invoke stop
➜ invoke build
➜ invoke start
```

Once the containers are up and running, you should now see the new plugin installed in your Nautobot instance.

!!! note
    You can even launch an `ngrok` service locally on your laptop, pointing to port 8080 (such as for chatops development), and it will point traffic directly to your Docker images.

### Updating Python Version

To update the Python version, you can update it within `tasks.py`.

```python
namespace = Collection("nautobot_golden_config")
namespace.configure(
    {
        "nautobot_golden_config": {
            ...
            "python_ver": "3.11",
	    ...
        }
    }
)
```

Or set the `INVOKE_NAUTOBOT_GOLDEN_CONFIG_PYTHON_VER` variable.

### Updating Nautobot Version

To update the Nautobot version, you can update it within `tasks.py`.

```python
namespace = Collection("nautobot_golden_config")
namespace.configure(
    {
        "nautobot_golden_config": {
            ...
            "nautobot_ver": "2.0.0",
	    ...
        }
    }
)
```

Or set the `INVOKE_NAUTOBOT_GOLDEN_CONFIG_NAUTOBOT_VER` variable.

## Other Miscellaneous Commands To Know

### Python Shell

To drop into a Django shell for Nautobot (in the Docker container) run:

```bash
➜ invoke nbshell
```

This is the same as running:

```bash
➜ invoke cli
➜ nautobot-server nbshell
```

### iPython Shell Plus

Django also has a more advanced shell that uses iPython and that will automatically import all the models:

```bash
➜ invoke shell-plus
```

This is the same as running:

```bash
➜ invoke cli
➜ nautobot-server shell_plus
```

### Tests

To run tests against your code, you can run all of the tests that TravisCI runs against any new PR with:

```bash
➜ invoke tests
```

To run an individual test, you can run any or all of the following:

```bash
➜ invoke unittest
➜ invoke bandit
➜ invoke black
➜ invoke flake8
➜ invoke pydocstyle
➜ invoke pylint
```
