"""
Custom exception handler для DRF.
Перехватывает DomainError и возвращает JSON с кодом ошибки.
"""
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

from common.exceptions import (
    NotFoundException,
    ConflictError,
    ValidationError,
    AuthenticationError,
    PermissionDeniedError,
)


def _map_exception(exception) -> dict:
    """Преобразует доменное исключение в структуру ответа."""
    return {
        "error": {
            "type": type(exception).__name__,
            "message": exception.message,
            "details": exception.details,
        }
    }


def drf_exception_handler(exc, context):
    """Обработчик исключений для DRF API."""
    # Сначала стандартный DRF handler
    response = exception_handler(exc, context)

    # Если это наше доменное исключение — формируем свой ответ
    if isinstance(exc, NotFoundException):
        return Response(_map_exception(exc), status=status.HTTP_404_NOT_FOUND)

    if isinstance(exc, ConflictError):
        return Response(_map_exception(exc), status=status.HTTP_409_CONFLICT)

    if isinstance(exc, ValidationError):
        return Response(_map_exception(exc), status=status.HTTP_422_UNPROCESSABLE_ENTITY)

    if isinstance(exc, AuthenticationError):
        return Response(_map_exception(exc), status=status.HTTP_401_UNAUTHORIZED)

    if isinstance(exc, PermissionDeniedError):
        return Response(_map_exception(exc), status=status.HTTP_403_FORBIDDEN)

    return response
