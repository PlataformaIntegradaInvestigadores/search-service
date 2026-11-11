from django.http import HttpRequest, HttpResponse
from django.views.decorators.http import require_GET

from common.admin_permission import ADMIN_TOKEN_HEADER, is_valid_admin_token


@require_GET
def validate_admin_token(request: HttpRequest) -> HttpResponse:
    token = request.META.get(ADMIN_TOKEN_HEADER, "")
    status = 204 if is_valid_admin_token(token) else 403
    return HttpResponse(status=status, headers={"Cache-Control": "no-store"})
