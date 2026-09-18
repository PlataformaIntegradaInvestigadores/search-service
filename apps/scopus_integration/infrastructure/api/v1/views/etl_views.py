import logging
import threading

from django.core.management import call_command
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

logger = logging.getLogger(__name__)

# Estado compartido dentro del proceso Django.
# En producción multi-worker usar Redis/DB; para TIC con un solo worker es suficiente.
_etl_lock = threading.Lock()
_etl_running = False
_last_run_at = None
_last_run_status = None  # 'success' | 'error' | None (nunca se ha ejecutado)


class EtlRunView(APIView):
    """
    POST  → dispara upsert_mongo en un hilo daemon y retorna 202 inmediatamente.
    GET   → reporta si el ETL sigue corriendo o ya terminó.
    """

    @extend_schema(
        summary="Iniciar ETL Neo4j → MongoDB",
        description=(
            "Ejecuta el comando upsert_mongo en segundo plano usando threading. "
            "Devuelve 202 Accepted de inmediato para no bloquear el cliente. "
            "Si ya hay una ejecución activa devuelve 409 Conflict."
        ),
        tags=["Admin – ETL"],
    )
    def post(self, request):
        global _etl_running

        if not _etl_lock.acquire(blocking=False):
            return Response(
                {
                    "status": "already_running",
                    "message": "El ETL ya está en ejecución.",
                },
                status=status.HTTP_409_CONFLICT,
            )

        _etl_running = True
        logger.info("ETL upsert_mongo iniciado por solicitud HTTP.")

        def _run():
            global _etl_running, _last_run_at, _last_run_status
            try:
                call_command("upsert_mongo")
                logger.info("ETL upsert_mongo finalizado exitosamente.")
                _last_run_status = "success"
            except Exception as exc:
                logger.error("ETL upsert_mongo falló: %s", exc, exc_info=True)
                _last_run_status = "error"
            finally:
                _last_run_at = timezone.now().isoformat()
                _etl_running = False
                _etl_lock.release()

        thread = threading.Thread(target=_run, daemon=True, name="etl-upsert-mongo")
        thread.start()

        return Response(
            {"status": "processing", "message": "ETL iniciado en segundo plano"},
            status=status.HTTP_202_ACCEPTED,
        )

    @extend_schema(
        summary="Estado del ETL",
        description=(
            'Devuelve {status: "running"|"idle"} para que el frontend pueda hacer polling, '
            "junto con la marca de tiempo y resultado de la última ejecución conocida."
        ),
        tags=["Admin – ETL"],
    )
    def get(self, request):
        return Response(
            {
                "status": "running" if _etl_running else "idle",
                "last_run_at": _last_run_at,
                "last_run_status": _last_run_status,
            },
            status=status.HTTP_200_OK,
        )
