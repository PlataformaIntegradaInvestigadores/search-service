"""Load the heavy search models in the background when a worker starts.

SciBERT, KeyBERT and the embeddings take about a minute to load. They used to be
loaded lazily on the first search of *each* Gunicorn worker, so users kept hitting
~30 s requests after every restart (and got a 500 if the models were missing).

They are loaded from a background thread started right after the worker forks
(see ``config/gunicorn.conf.py``), not before Gunicorn binds its port: the deploy
pipeline checks ``/health/`` about a minute after starting the container and rolls
back on failure, so the server has to answer immediately while the models load.

A failure to load must not affect the worker: health and every route that does
not need the models keep working, and the first search retries.
"""

import logging
import os
import threading

logger = logging.getLogger(__name__)


def preload_enabled() -> bool:
    return os.environ.get("SEARCH_PRELOAD_MODELS", "True").lower() not in (
        "0",
        "false",
        "no",
    )


def preload_models() -> bool:
    """Instantiate the LLM search singleton. Returns True when it is ready."""
    if not preload_enabled():
        logger.info("Precarga de modelos desactivada (SEARCH_PRELOAD_MODELS)")
        return False

    try:
        from apps.search_engine.application.services.llm_search_service import (
            LLMSearchService,
        )

        LLMSearchService()
    except Exception:
        logger.exception(
            "No se pudieron precargar los modelos; se cargarán en la primera búsqueda"
        )
        return False

    logger.info("Modelos de búsqueda precargados")
    return True


def preload_models_in_background() -> threading.Thread | None:
    """Start :func:`preload_models` in a daemon thread. Returns it (or None)."""
    if not preload_enabled():
        logger.info("Precarga de modelos desactivada (SEARCH_PRELOAD_MODELS)")
        return None

    thread = threading.Thread(target=preload_models, name="model-preload", daemon=True)
    thread.start()
    return thread
