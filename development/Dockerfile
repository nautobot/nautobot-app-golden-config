ARG PYTHON_VER
ARG NAUTOBOT_VER
FROM ghcr.io/nautobot/nautobot-dev:${NAUTOBOT_VER}-py${PYTHON_VER}

WORKDIR /source

# Copy in only pyproject.toml/poetry.lock to help with caching this layer if no updates to dependencies
COPY poetry.lock pyproject.toml /source/
# --no-root declares not to install the project package since we're wanting to take advantage of caching dependency installation
# and the project is copied in and installed after this step
RUN poetry install --no-interaction --no-ansi --no-root

# Copy in the rest of the source code and install local Nautobot plugin
COPY . /source
RUN poetry install --no-interaction --no-ansi

RUN apt update
RUN apt install -y libmariadb-dev-compat gcc
RUN pip install mysqlclient

COPY development/nautobot_config.py /opt/nautobot/nautobot_config.py
