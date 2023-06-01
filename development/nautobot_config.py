"""Nautobot development configuration file."""
# pylint: disable=invalid-envvar-default
import os
import sys

from nautobot.core.settings import *  # noqa: F403
from nautobot.core.settings_funcs import parse_redis_connection


#
# Misc. settings
#

ALLOWED_HOSTS = os.getenv("NAUTOBOT_ALLOWED_HOSTS", "").split(" ")
SECRET_KEY = os.getenv("NAUTOBOT_SECRET_KEY", "")


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
            "NAUTOBOT_DB_PORT", default_db_settings[nautobot_db_engine]["NAUTOBOT_DB_PORT"]
        ),  # Database port, default to postgres
        "CONN_MAX_AGE": int(os.getenv("NAUTOBOT_DB_TIMEOUT", 300)),  # Database timeout
        "ENGINE": nautobot_db_engine,
    }
}

# Ensure proper Unicode handling for MySQL
if DATABASES["default"]["ENGINE"] == "django.db.backends.mysql":
    DATABASES["default"]["OPTIONS"] = {"charset": "utf8mb4"}

#
# Debug
#

DEBUG = True

# Django Debug Toolbar
DEBUG_TOOLBAR_CONFIG = {"SHOW_TOOLBAR_CALLBACK": lambda _request: DEBUG and not TESTING}

if DEBUG and "debug_toolbar" not in INSTALLED_APPS:  # noqa: F405
    INSTALLED_APPS.append("debug_toolbar")  # noqa: F405
if DEBUG and "debug_toolbar.middleware.DebugToolbarMiddleware" not in MIDDLEWARE:  # noqa: F405
    MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")  # noqa: F405

#
# Logging
#

LOG_LEVEL = "DEBUG" if DEBUG else "INFO"

TESTING = len(sys.argv) > 1 and sys.argv[1] == "test"

# Verbose logging during normal development operation, but quiet logging during unit test execution
if not TESTING:
    LOGGING = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "normal": {
                "format": "%(asctime)s.%(msecs)03d %(levelname)-7s %(name)s :\n  %(message)s",
                "datefmt": "%H:%M:%S",
            },
            "verbose": {
                "format": "%(asctime)s.%(msecs)03d %(levelname)-7s %(name)-20s %(filename)-15s %(funcName)30s() :\n  %(message)s",
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
else:
    LOGGING = {}

#
# Redis
#

# The django-redis cache is used to establish concurrent locks using Redis. The
# django-rq settings will use the same instance/database by default.
#
# This "default" server is now used by RQ_QUEUES.
# >> See: nautobot.core.settings.RQ_QUEUES
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": parse_redis_connection(redis_database=0),
        "TIMEOUT": 300,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    }
}

# RQ_QUEUES is not set here because it just uses the default that gets imported
# up top via `from nautobot.core.settings import *`.

# Redis Cacheops
CACHEOPS_REDIS = parse_redis_connection(redis_database=1)

#
# Celery settings are not defined here because they can be overloaded with
# environment variables. By default they use `CACHES["default"]["LOCATION"]`.
#


# Enable installed plugins. Add the name of each plugin to the list.
PLUGINS = ["nautobot_plugin_nornir", "nautobot_golden_config"]

# Plugins configuration settings. These settings are used by various plugins that the user may have installed.
# Each key in the dictionary is the name of an installed plugin and its value is a dictionary of settings.
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
        # dispatcher_mapping may be necessary if you get an error `Cannot import "<foo>". Is the library installed?`
        # when you run a backup job, and <foo> is the name of the platform applied to the device.
        # to the Nornir driver names ("arista_eos", "cisco_ios", etc.).
        # "dispatcher_mapping": {
        #     "eos": "nornir_nautobot.plugins.tasks.dispatcher.arista_eos.NautobotNornirDriver",
        #     "arbitrary_platform_name": "nornir_nautobot.plugins.tasks.dispatcher.arista_eos.NautobotNornirDriver",
        #     "ios": "nornir_nautobot.plugins.tasks.dispatcher.cisco_ios.NautobotNornirDriver",
        #     "iosxe": "nornir_nautobot.plugins.tasks.dispatcher.cisco_ios.NautobotNornirDriver",
        #     "junos": "nornir_nautobot.plugins.tasks.dispatcher.juniper_junos.NautobotNornirDriver",
        #     "nxos": "nornir_nautobot.plugins.tasks.dispatcher.cisco_nxos.NautobotNornirDriver",
        # },
    },
    "nautobot_golden_config": {
        "per_feature_bar_width": float(os.environ.get("PER_FEATURE_BAR_WIDTH", 0.15)),
        "per_feature_width": int(os.environ.get("PER_FEATURE_WIDTH", 13)),
        "per_feature_height": int(os.environ.get("PER_FEATURE_HEIGHT", 4)),
        "enable_backup": is_truthy(os.environ.get("ENABLE_BACKUP", True)),
        "enable_compliance": is_truthy(os.environ.get("ENABLE_COMPLIANCE", True)),
        "enable_intended": is_truthy(os.environ.get("ENABLE_INTENDED", True)),
        "enable_sotagg": is_truthy(os.environ.get("ENABLE_SOTAGG", True)),
        "sot_agg_transposer": os.environ.get("SOT_AGG_TRANSPOSER"),
        "enable_postprocessing": is_truthy(os.environ.get("ENABLE_POSTPROCESSING", True)),
        "postprocessing_callables": os.environ.get("POSTPROCESSING_CALLABLES", []),
        "postprocessing_subscribed": os.environ.get("POSTPROCESSING_SUBSCRIBED", []),
        "sync_config_context_repos": is_truthy(os.environ.get("SYNC_CONFIG_CONTEXT_REPOS", False)),
        # The platform_slug_map maps an arbitrary platform slug to its corresponding parser.
        # Use this if the platform slug names in your Nautobot instance don't correspond exactly
        # to the Nornir driver names ("arista_eos", "cisco_ios", etc.).
        # Each key should == the slug of the Nautobot platform object.
        # "platform_slug_map": {
        #     "eos": "arista_eos",
        #     "ios": "cisco_ios",
        #     "iosxe": "cisco_ios",
        #     "junos": "juniper_junos",
        #     "nxos": "cisco_nxos",
        # },
        # "get_custom_compliance": "my.custom_compliance.func",
    },
}

# Modify django_jinja Environment for test cases
django_jinja_config = None
for template in TEMPLATES:
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
from nautobot_golden_config.tests import jinja_filters  # noqa: E402
