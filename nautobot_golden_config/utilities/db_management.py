"""Functions to manage DB related tasks."""
from django.db import connections
from nautobot_plugin_nornir.constants import NORNIR_SETTINGS


RUNNER_SETTINGS = NORNIR_SETTINGS.get("runner", {})


def close_threaded_db_connections(func):
    """Decorator that clears idle DB connections in thread."""

    def inner(*args, **kwargs):
        """Inner function."""
        try:
            func(*args, **kwargs)

        finally:
            # Only clear DB connections if plays are threaded
            if RUNNER_SETTINGS.get("plugin") == "threaded":
                connections.close_all()

    return inner
