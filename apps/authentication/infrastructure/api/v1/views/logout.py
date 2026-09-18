from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView


class LogoutView(APIView):
    @extend_schema(tags=["Authentication"])
    def post(self, request):
        return Response({"detail": "Logout exitoso"}, status=status.HTTP_200_OK)
