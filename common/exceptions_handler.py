from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

from apps.common.exceptions import (
    NotFoundException,
    ConflictError,
    ValidationError,
    AuthenticationError,
    PermissionDeniedError,
)


def _build_response(exception) -> dict:
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


def drf_exception_handler(exc, context):
    response = exception_handler(exc, context)

    status_code = _ERROR_MAP.get(type(exc))
    if status_code is not None:
        return Response(_build_response(exc), status=status_code)

    return response
