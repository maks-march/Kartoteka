"""Middleware перевода доменных исключений в JSON-ответы (для не-DRF путей)."""
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
    """Ловит доменные исключения и отдаёт единый JSON с нужным HTTP-кодом."""

    def __init__(self, get_response):
        """Сохраняет следующий обработчик в цепочке middleware."""
        self.get_response = get_response

    def __call__(self, request):
        """Пропускает запрос дальше по цепочке обработчиков."""
        return self.get_response(request)

    def process_exception(self, request, exception):
        """Переводит доменное исключение в JSON-ответ; иначе возвращает None."""
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
