ARG python_ver=3.7
FROM python:${python_ver}

# Set env vars that won't change per image
ENV PYTHONUNBUFFERED=1 \
    PATH="/root/.poetry/bin:$PATH" \
    NAUTOBOT_CONFIG="/source/development/nautobot_config.py"

RUN pip install --upgrade pip\
  && pip install poetry

# -------------------------------------------------------------------------------------
# Install Nautobot Plugin
# -------------------------------------------------------------------------------------
RUN mkdir -p /source
RUN git clone https://github.com/nautobot/nornir-nautobot -b nextgen --single-branch nornir-nautobot
RUN pip install ./nornir-nautobot/packages/netutils-0.1.0-py3-none-any.whl
WORKDIR /source
COPY . /source
RUN poetry config virtualenvs.create false \
  && poetry install --no-interaction --no-ansi
RUN rm -rf /usr/local/lib/python3.7/site-packages/nornir_nautobot \
  && mv /nornir-nautobot/nornir_nautobot /usr/local/lib/python3.7/site-packages/nornir_nautobot
