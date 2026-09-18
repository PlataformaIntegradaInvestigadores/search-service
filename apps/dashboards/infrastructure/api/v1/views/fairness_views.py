"""Vistas del dashboard de fairness (mitigacion de sesgos).

Sirven los resultados pre-calculados de los notebooks S5-S10 (Proyecto Centinela,
componente de mitigacion de sesgos) desde un JSON consolidado. No recalculan nada:
el analisis vive en bias_analysis/ y aqui solo se expone para el modulo admin.
"""

import json
from functools import lru_cache
from pathlib import Path

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

# apps/dashboards/infrastructure/api/v1/views/fairness_views.py -> apps/dashboards
_DASHBOARDS_DIR = Path(__file__).resolve().parents[4]
_DATA_FILE = _DASHBOARDS_DIR / "fairness_data" / "fairness_dashboard.json"


@lru_cache(maxsize=1)
def _load_fairness_data():
    with open(_DATA_FILE, encoding="utf-8") as fh:
        return json.load(fh)


def _safe(section=None):
    """Carga el JSON y devuelve la seccion pedida (o todo). (data, error_response)."""
    try:
        data = _load_fairness_data()
    except FileNotFoundError:
        return None, Response(
            {
                "success": False,
                "message": "Datos de fairness no disponibles. "
                "Ejecute gen_fairness_json.py en bias_analysis.",
            },
            status=status.HTTP_404_NOT_FOUND,
        )
    if section is None:
        return data, None
    return {k: data[k] for k in section if k in data}, None


@extend_schema(tags=["fairness"], summary="Resultados consolidados de fairness (todo)")
class FairnessSummaryView(APIView):
    def get(self, request):
        data, err = _safe()
        return err or Response(data)


@extend_schema(
    tags=["fairness"], summary="Linea base de equidad (diagnostico S5) + SHAP"
)
class FairnessBaselineView(APIView):
    def get(self, request):
        data, err = _safe(["meta", "baseline", "shap"])
        return err or Response(data)


@extend_schema(
    tags=["fairness"], summary="Impacto antes/despues, veredicto y seleccion (S10)"
)
class FairnessMitigationView(APIView):
    def get(self, request):
        data, err = _safe(["meta", "impact", "verdict", "selection"])
        return err or Response(data)


@extend_schema(
    tags=["fairness"], summary="Barridos de sensibilidad de alpha y lambda (S10)"
)
class FairnessSensitivityView(APIView):
    def get(self, request):
        data, err = _safe(["meta", "model_mitigation", "search_mitigation"])
        return err or Response(data)
