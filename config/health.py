import logging

from django.http import JsonResponse
from neomodel import db

logger = logging.getLogger(__name__)


def health_check(request):
    try:
        db.cypher_query("RETURN 1")
    except Exception:
        logger.exception("Health check failed")
        return JsonResponse({"status": "error"}, status=503)
    return JsonResponse({"status": "ok"})
