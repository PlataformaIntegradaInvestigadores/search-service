import base64
import binascii
import hmac
import os

from rest_framework.permissions import BasePermission


class IsCentinelaAdmin(BasePermission):
    """Gates admin-only endpoints (datalake repopulation, ETL triggers, ...)
    behind the same ADMIN_CENTINELA/PASSWORD_CENTINELA pair LoginView already
    checks, via HTTP Basic Auth. No session/JWT is issued or required
    elsewhere in this service, so this avoids inventing a parallel auth
    mechanism; it only stops the endpoint from being reachable by anyone with
    the gateway's public URL.
    """

    message = "Admin credentials required."

    def has_permission(self, request, view) -> bool:
        admin_centinela = os.environ.get("ADMIN_CENTINELA")
        password_centinela = os.environ.get("PASSWORD_CENTINELA")
        if not admin_centinela or not password_centinela:
            return False

        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        scheme, _, credentials = auth_header.partition(" ")
        if scheme.lower() != "basic" or not credentials:
            return False

        try:
            decoded = base64.b64decode(credentials).decode("utf-8")
        except (binascii.Error, UnicodeDecodeError):
            return False

        username, _, password = decoded.partition(":")
        return hmac.compare_digest(username, admin_centinela) and hmac.compare_digest(
            password, password_centinela
        )
