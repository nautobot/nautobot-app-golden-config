"""Nautobot development configuration file."""

import os
import sys

from nautobot.core.settings import *  # noqa: F403  # pylint: disable=wildcard-import,unused-wildcard-import
from nautobot.core.settings_funcs import is_truthy

#
# Debug
#

DEBUG = is_truthy(os.getenv("NAUTOBOT_DEBUG", "false"))
_TESTING = len(sys.argv) > 1 and sys.argv[1] == "test"

if DEBUG and not _TESTING:
    DEBUG_TOOLBAR_CONFIG = {"SHOW_TOOLBAR_CALLBACK": lambda _request: True}

    if "debug_toolbar" not in INSTALLED_APPS:  # noqa: F405
        INSTALLED_APPS.append("debug_toolbar")  # noqa: F405
    if "debug_toolbar.middleware.DebugToolbarMiddleware" not in MIDDLEWARE:  # noqa: F405
        MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")  # noqa: F405

#
# Misc. settings
#

ALLOWED_HOSTS = os.getenv("NAUTOBOT_ALLOWED_HOSTS", "").split(" ")
SECRET_KEY = os.getenv("NAUTOBOT_SECRET_KEY", "")

#
# Database
#

nautobot_db_engine = os.getenv("NAUTOBOT_DB_ENGINE", "django.db.backends.postgresql")
default_db_settings = {
    "django.db.backends.postgresql": {
        "NAUTOBOT_DB_PORT": "5432",
    },
    "django.db.backends.mysql": {
        "NAUTOBOT_DB_PORT": "3306",
    },
}
DATABASES = {
    "default": {
        "NAME": os.getenv("NAUTOBOT_DB_NAME", "nautobot"),  # Database name
        "USER": os.getenv("NAUTOBOT_DB_USER", ""),  # Database username
        "PASSWORD": os.getenv("NAUTOBOT_DB_PASSWORD", ""),  # Database password
        "HOST": os.getenv("NAUTOBOT_DB_HOST", "localhost"),  # Database server
        "PORT": os.getenv(
            "NAUTOBOT_DB_PORT",
            default_db_settings[nautobot_db_engine]["NAUTOBOT_DB_PORT"],
        ),  # Database port, default to postgres
        "CONN_MAX_AGE": int(os.getenv("NAUTOBOT_DB_TIMEOUT", "300")),  # Database timeout
        "ENGINE": nautobot_db_engine,
    }
}

# Ensure proper Unicode handling for MySQL
if DATABASES["default"]["ENGINE"] == "django.db.backends.mysql":
    DATABASES["default"]["OPTIONS"] = {"charset": "utf8mb4"}

#
# Redis
#

# The django-redis cache is used to establish concurrent locks using Redis.
# Inherited from nautobot.core.settings
# CACHES = {....}

#
# Celery settings are not defined here because they can be overloaded with
# environment variables. By default they use `CACHES["default"]["LOCATION"]`.
#

#
# Logging
#

LOG_LEVEL = "DEBUG" if DEBUG else "INFO"

# Verbose logging during normal development operation, but quiet logging during unit test execution
if not _TESTING:
    LOGGING = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "normal": {
                "format": "%(asctime)s.%(msecs)03d %(levelname)-7s %(name)s : %(message)s",
                "datefmt": "%H:%M:%S",
            },
            "verbose": {
                "format": "%(asctime)s.%(msecs)03d %(levelname)-7s %(name)-20s %(filename)-15s %(funcName)30s() : %(message)s",
                "datefmt": "%H:%M:%S",
            },
        },
        "handlers": {
            "normal_console": {
                "level": "INFO",
                "class": "logging.StreamHandler",
                "formatter": "normal",
            },
            "verbose_console": {
                "level": "DEBUG",
                "class": "logging.StreamHandler",
                "formatter": "verbose",
            },
        },
        "loggers": {
            "django": {"handlers": ["normal_console"], "level": "INFO"},
            "nautobot": {
                "handlers": ["verbose_console" if DEBUG else "normal_console"],
                "level": LOG_LEVEL,
            },
        },
    }

#
# Apps
#

# Enable installed apps. Add the name of each app to the list.
PLUGINS = ["nautobot_plugin_nornir", "nautobot_golden_config"]

# Apps configuration settings. These settings are used by various apps that the user may have installed.
# Each key in the dictionary is the name of an installed app and its value is a dictionary of settings.
PLUGINS_CONFIG = {
    "nautobot_plugin_nornir": {
        "nornir_settings": {
            "credentials": "nautobot_plugin_nornir.plugins.credentials.env_vars.CredentialsEnvVars",
            "runner": {
                "plugin": "threaded",
                "options": {
                    "num_workers": 20,
                },
            },
        },
    },
    "nautobot_golden_config": {
        "per_feature_bar_width": float(os.environ.get("PER_FEATURE_BAR_WIDTH", 0.15)),
        "per_feature_width": int(os.environ.get("PER_FEATURE_WIDTH", 13)),
        "per_feature_height": int(os.environ.get("PER_FEATURE_HEIGHT", 4)),
        "enable_backup": is_truthy(os.environ.get("ENABLE_BACKUP", True)),
        "enable_compliance": is_truthy(os.environ.get("ENABLE_COMPLIANCE", True)),
        "enable_intended": is_truthy(os.environ.get("ENABLE_INTENDED", True)),
        "enable_sotagg": is_truthy(os.environ.get("ENABLE_SOTAGG", True)),
        "enable_postprocessing": is_truthy(os.environ.get("ENABLE_POSTPROCESSING", True)),
        "enable_plan": is_truthy(os.environ.get("ENABLE_PLAN", True)),
        "enable_deploy": is_truthy(os.environ.get("ENABLE_DEPLOY", True)),
        "sot_agg_transposer": os.environ.get("SOT_AGG_TRANSPOSER"),
        "postprocessing_callables": os.environ.get("POSTPROCESSING_CALLABLES", []),
        "postprocessing_subscribed": os.environ.get("POSTPROCESSING_SUBSCRIBED", []),
        "jinja_env": {
            "undefined": "jinja2.StrictUndefined",
            "trim_blocks": is_truthy(os.getenv("NAUTOBOT_JINJA_ENV_TRIM_BLOCKS", "true")),
            "lstrip_blocks": is_truthy(os.getenv("NAUTOBOT_JINJA_ENV_LSTRIP_BLOCKS", "false")),
        },
        # "get_custom_compliance": "my.custom_compliance.func",
        # "default_deploy_status": "Not Approved",
        #
        #
        # custom_dispatcher is not required for preferring a framework such as netmiko or napalm.
        # Instead, this is only required if you are truly "rolling your own" dispatcher, potentially
        # to accommodate OS's not currently supported or to add your own business logic.
        # "custom_dispatcher": {
        #     "arista_eos": "my_custom.dispatcher.NornirDriver",
        #     "arbitrary_platform_name": "my_custom.dispatcher.OtherNornirDriver",
        # }
    },
}

# TODO:Verify this is still needed
# Modify django_jinja Environment for test cases
django_jinja_config = None
for template in TEMPLATES:  # noqa: F405
    if template["BACKEND"].startswith("django_jinja"):
        django_jinja_config = template

if django_jinja_config is not None:
    jinja_options = django_jinja_config.get("OPTIONS")
    if not jinja_options:
        jinja_options = {}
        django_jinja_config["OPTIONS"] = jinja_options
    # Default behavior ignores UndefinedErrors
    jinja_options["undefined"] = "jinja2.StrictUndefined"

# Import filter function to have it register filter with django_jinja
from nautobot_golden_config.tests import jinja_filters  # noqa: E402, F401
