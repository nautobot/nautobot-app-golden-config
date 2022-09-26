"""Functions to manage DB related tasks."""
from django.db import connections


def close_threaded_db_connections(func):
    """Decorator that clears idle DB connections in thread."""

    def inner(*args, **kwargs):
        """Inner function."""
        try:
            func(*args, **kwargs)

        finally:
            connections.close_all()

    return inner
