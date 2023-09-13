# -------------------------------------------------------------------------------------
# Nautobot App Developement Dockerfile Template
# Version: 1.1.0
#
# Apps that need to add additional steps or packages can do in the section below.
# -------------------------------------------------------------------------------------
# !!! USE CAUTION WHEN MODIFYING LINES BELOW

# Accepts a desired Nautobot version as build argument, default to 1.4.0
ARG NAUTOBOT_VER="1.4.0"

# Accepts a desired Python version as build argument, default to 3.8
ARG PYTHON_VER="3.8"

# Retrieve published development image of Nautobot base which should include most CI dependencies
FROM ghcr.io/nautobot/nautobot-dev:${NAUTOBOT_VER}-py${PYTHON_VER}

# Runtime argument and environment setup
ARG NAUTOBOT_ROOT=/opt/nautobot

ENV prometheus_multiproc_dir=/prom_cache
ENV NAUTOBOT_ROOT ${NAUTOBOT_ROOT}

# Install Poetry manually via its installer script;
# We might be using an older version of Nautobot that includes an older version of Poetry
# and CI and local development may have a newer version of Poetry
# Since this is only used for development and we don't ship this container, pinning Poetry back is not expressly necessary
# We also don't need virtual environments in container
RUN curl -sSL https://install.python-poetry.org | python3 - && \
  poetry config virtualenvs.create false

# !!! USE CAUTION WHEN MODIFYING LINES ABOVE
# -------------------------------------------------------------------------------------
# App-specifc system build/test dependencies.
# 
# Example: LDAP requires `libldap2-dev` to be apt-installed before the Python package.
# -------------------------------------------------------------------------------------
# --> Start safe to modify section

# Uncomment the lines below if you are apt-installing any package.
# RUN apt-get -y update && apt-get -y install \
#     libldap2-dev \
#     && rm -rf /var/lib/apt/lists/*

# --> Stop safe to modify section
# -------------------------------------------------------------------------------------
# Install Nautobot App
# -------------------------------------------------------------------------------------
# !!! USE CAUTION WHEN MODIFYING LINES BELOW

# Copy in the source code
WORKDIR /source
COPY . /source

# Get container's installed Nautobot version as a forced constraint
# NAUTOBOT_VER may be a branch name and not a published release therefor we need to get the installed version
#  so pip can use it to recognize local constraints.
RUN pip show nautobot | grep "^Version: " | sed -e 's/Version: /nautobot==/' > constraints.txt

# Use Poetry to grab dev dependencies from the lock file
# Can be improved in Poetry 1.2 which allows `poetry install --only dev`
#
# We can't use the entire freeze as it takes forever to resolve with rigidly fixed non-direct dependencies,
#   especially those that are only direct to Nautobot but the container included versions slightly mismatch
RUN poetry export -f requirements.txt --without-hashes --output poetry_freeze_base.txt
RUN poetry export -f requirements.txt --with dev --without-hashes --output poetry_freeze_all.txt
RUN sort poetry_freeze_base.txt poetry_freeze_all.txt | uniq -u > poetry_freeze_dev.txt

# Install all local project as editable, constrained on Nautobot version, to get any additional
#   direct dependencies of the app
RUN pip install -c constraints.txt -e .

# Install any dev dependencies frozen from Poetry
# Can be improved in Poetry 1.2 which allows `poetry install --only dev`
RUN pip install -c constraints.txt -r poetry_freeze_dev.txt

COPY development/nautobot_config.py ${NAUTOBOT_ROOT}/nautobot_config.py
# !!! USE CAUTION WHEN MODIFYING LINES ABOVE
