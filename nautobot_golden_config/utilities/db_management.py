"""Functions to manage DB related tasks."""
from django.db import connections


def close_threaded_db_connections(func):
    """Decorator that clears idle DB connections in thread."""
    def inner(*args, **kwargs):
        """Inner function."""
        func(*args, **kwargs)

        for c in connections.all():
            c.connection.close()

    return inner
