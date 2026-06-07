"""Middleware для обработки доменных исключений и возврата HTTP-ответов."""

import json
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


class DomainExceptionMiddleware:
    """
    Перехватывает DomainError из usecase-слоя и возвращает 
    соответствующий HTTP-ответ с кодом ошибки.
    """

    ERROR_MAP = {
        NotFoundException: 404,
        ConflictError: 409,
        ValidationError: 422,
        AuthenticationError: 401,
        PermissionDeniedError: 403,
    }

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        status_code = self.ERROR_MAP.get(type(exception))
        if status_code is None:
            return None  # Не наша ошибка — пусть Django обрабатывает

        logger.warning(
            "DomainException: %s | %s | path=%s",
            type(exception).__name__,
            str(exception),
            request.path,
        )

        body = {
            "error": {
                "type": type(exception).__name__,
                "message": exception.message,
                "details": exception.details,
            }
        }
        return JsonResponse(body, status=status_code)
