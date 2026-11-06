"""MongoDB connection options."""

import os

# pymongo waits 30 s to find a server by default. When MongoDB is down that made
# /health/ hang for half a minute and kept the Gunicorn workers busy, so the BFF and
# the gateway timed out instead of seeing a clean "degraded". MongoDB runs next to
# this service on the Docker network, so a few seconds is plenty.
DEFAULT_SERVER_SELECTION_TIMEOUT_MS = 3000


def server_selection_timeout_ms(environ=None) -> int:
    """Value of MONGO_SERVER_SELECTION_TIMEOUT_MS, or the default if unset/invalid."""
    environ = os.environ if environ is None else environ
    try:
        value = int(environ.get("MONGO_SERVER_SELECTION_TIMEOUT_MS", ""))
    except ValueError:
        return DEFAULT_SERVER_SELECTION_TIMEOUT_MS
    return value if value > 0 else DEFAULT_SERVER_SELECTION_TIMEOUT_MS
