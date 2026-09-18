import os

from dotenv import load_dotenv
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.authentication.infrastructure.api.v1.serializers.login_request_serializer import (
    LoginRequestSerializer,
)

load_dotenv()


class LoginView(APIView):
    @extend_schema(request=LoginRequestSerializer, tags=["Authentication"])
    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        admin_centinela = os.environ.get("ADMIN_CENTINELA")
        password_centinela = os.environ.get("PASSWORD_CENTINELA")

        if username == admin_centinela and password == password_centinela:
            return Response({"message": "Login Succesfull"}, status=status.HTTP_200_OK)
        return Response(
            {"message": "Invalid Credentials"}, status=status.HTTP_400_BAD_REQUEST
        )
