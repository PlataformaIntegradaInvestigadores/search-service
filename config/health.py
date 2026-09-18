import logging
import socket

from django.http import JsonResponse
from mongoengine.connection import get_db
from neomodel import db

logger = logging.getLogger(__name__)


def _local_ip() -> str:
    try:
        return socket.gethostbyname(socket.gethostname())
    except OSError:
        return "unknown"


def health_check(request):
    try:
        db.cypher_query("RETURN 1")
        neo4j_status = "ok"
    except Exception:
        logger.exception("Health check Neo4j failure")
        neo4j_status = "error"

    try:
        get_db().command("ping")
        mongo_status = "ok"
    except Exception:
        logger.exception("Health check MongoDB failure")
        mongo_status = "error"

    statuses = {neo4j_status, mongo_status}
    if statuses == {"ok"}:
        group_status, global_status, http_status = "Operativo", "Online", 200
    elif "ok" in statuses:
        group_status, global_status, http_status = "Degradado", "Degraded", 503
    else:
        group_status, global_status, http_status = "Caído", "Offline", 503

    payload = {
        "server_name": "search-service",
        "ip_address": _local_ip(),
        "global_status": global_status,
        "groups": [
            {
                "group_name": "Motor de Búsqueda",
                "group_status": group_status,
                "services": [
                    {"name": "neo4j", "status": neo4j_status},
                    {"name": "mongodb", "status": mongo_status},
                ],
            }
        ],
    }
    return JsonResponse(payload, status=http_status)
