"""Gunicorn hooks (loaded with ``-c config/gunicorn.conf.py``)."""


def post_fork(server, worker):
    # Threads do not survive fork, so this has to run in each worker.
    from apps.search_engine.application.preload import preload_models_in_background

    preload_models_in_background()
