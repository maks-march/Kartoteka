import logging
from django.http import JsonResponse

from common.exceptions import (
    NotFoundException,
    ConflictError,
    ValidationError,
    AuthenticationError,
    PermissionDeniedError,
)

logger = logging.getLogger(__name__)

_ERROR_MAP = {
    NotFoundException: 404,
    ConflictError: 409,
    ValidationError: 422,
    AuthenticationError: 401,
    PermissionDeniedError: 403,
}


class DomainExceptionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        status_code = _ERROR_MAP.get(type(exception))
        if status_code is None:
            return None

        logger.warning("DomainException: %s | %s | path=%s", type(exception).__name__, str(exception), request.path)

        return JsonResponse({
            "error": {
                "type": type(exception).__name__,
                "message": exception.message,
                "details": exception.details,
            }
        }, status=status_code)
