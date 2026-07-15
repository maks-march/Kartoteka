"""Обработчик исключений DRF: перевод доменных ошибок в HTTP-ответы."""
from django.core.exceptions import ValidationError as DjangoValidationError
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


def _build_response(exception) -> dict:
    """Формирует унифицированное тело ответа об ошибке (вспомогательная)."""
    return {
        "error": {
            "type": type(exception).__name__,
            "message": exception.message,
            "details": exception.details,
        }
    }


_ERROR_MAP = {
    NotFoundException: status.HTTP_404_NOT_FOUND,
    ConflictError: status.HTTP_409_CONFLICT,
    ValidationError: status.HTTP_422_UNPROCESSABLE_ENTITY,
    AuthenticationError: status.HTTP_401_UNAUTHORIZED,
    PermissionDeniedError: status.HTTP_403_FORBIDDEN,
}


def _django_validation_message(exc) -> str:
    """Извлекает читаемое сообщение из django ValidationError (вспомогательная)."""
    if hasattr(exc, "message_dict"):
        return exc.message_dict
    messages = getattr(exc, "messages", None)
    if messages:
        return messages[0] if len(messages) == 1 else messages
    return str(exc)


def drf_exception_handler(exc, context):
    """Обработчик исключений DRF: маппит доменные и django-ошибки на HTTP-коды."""
    # Доменные исключения с явным маппингом на HTTP-коды.
    status_code = _ERROR_MAP.get(type(exc))
    if status_code is not None:
        return Response(_build_response(exc), status=status_code)

    # Бизнес-логика (use cases) местами бросает django.core.exceptions.ValidationError.
    # DRF её не понимает и без обработки она превращается в 500.
    # Приводим к единому формату ответа и коду 422.
    if isinstance(exc, DjangoValidationError):
        return Response(
            {
                "error": {
                    "type": "ValidationError",
                    "message": _django_validation_message(exc),
                    "details": "",
                }
            },
            status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    return exception_handler(exc, context)
