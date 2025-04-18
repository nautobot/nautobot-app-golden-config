# -------------------------------------------------------------------------------------
# Nautobot App Developement Dockerfile Template
# Version: 1.1.0
#
# Apps that need to add additional steps or packages can do in the section below.
# -------------------------------------------------------------------------------------
# !!! USE CAUTION WHEN MODIFYING LINES BELOW

# Accepts a desired Nautobot version as build argument, default to 3.0.0
# TODO: Change to 3.0.0 after v3.0.0 is released
ARG NAUTOBOT_VER="next"

# Accepts a desired Python version as build argument, default to 3.11
ARG PYTHON_VER="3.11"

# Retrieve published development image of Nautobot base which should include most CI dependencies
FROM ghcr.io/nautobot/nautobot-dev:${NAUTOBOT_VER}-py${PYTHON_VER}

# Runtime argument and environment setup
ARG NAUTOBOT_ROOT=/opt/nautobot

ENV prometheus_multiproc_dir=/prom_cache
ENV NAUTOBOT_ROOT=${NAUTOBOT_ROOT}
ENV INVOKE_NAUTOBOT_GOLDEN_CONFIG_LOCAL=true

# Install Poetry manually via its installer script;
# We might be using an older version of Nautobot that includes an older version of Poetry
# and CI and local development may have a newer version of Poetry
# Since this is only used for development and we don't ship this container, pinning Poetry back is not expressly necessary
# We also don't need virtual environments in container
RUN which poetry || curl -sSL https://install.python-poetry.org | python3 - && \
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

# Build args must be declared in each stage
ARG NAUTOBOT_VER
ARG PYTHON_VER

# Constrain the Nautobot version to NAUTOBOT_VER, fall back to installing from git branch if not available on PyPi
# In CI, this should be done outside of the Dockerfile to prevent cross-compile build failures
ARG CI
RUN if [ -z "${CI+x}" ]; then \
    INSTALLED_NAUTOBOT_VER=$(pip show nautobot | grep "^Version" | sed "s/Version: //"); \
    poetry add --lock nautobot@${INSTALLED_NAUTOBOT_VER} --python ${PYTHON_VER} || \
    poetry add --lock git+https://github.com/nautobot/nautobot.git#${NAUTOBOT_VER} --python ${PYTHON_VER}; fi

# Install the app
RUN poetry install --extras all --with dev

COPY development/nautobot_config.py ${NAUTOBOT_ROOT}/nautobot_config.py
# !!! USE CAUTION WHEN MODIFYING LINES ABOVE
