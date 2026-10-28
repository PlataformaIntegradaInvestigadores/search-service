from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.scopus_integration.application.services.model_generation_service import (
    ModelGenerationService,
)
from common.admin_permission import IsCentinelaAdmin


class GenerateModelView(APIView):
    # Solo administracion: IsCentinelaAdmin acepta el token de LoginView o HTTP Basic;
    # sin authentication_classes la BasicAuthentication por defecto de DRF
    # intercepta la cabecera Authorization antes de que corra el permiso.
    authentication_classes = []
    permission_classes = [IsCentinelaAdmin]

    @extend_schema(
        summary="Generate model",
        tags=["TF-IDF"],
    )
    def post(self, request):
        try:
            model_generator = ModelGenerationService()
            corpus = model_generator.read_path()
            model_generator.generate_model(corpus)
            return Response({"success": True}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"success": False, "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
