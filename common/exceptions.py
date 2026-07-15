"""Доменные исключения приложения.

Единая иерархия ошибок бизнес-логики (use cases), не зависящая от HTTP.
В HTTP-коды они переводятся отдельно — в обработчике DRF и middleware.
"""


class DomainError(Exception):
    """Базовое доменное исключение с сообщением и деталями."""

    def __init__(self, message="", details=""):
        """Сохраняет человекочитаемое сообщение и дополнительные детали ошибки."""
        self.message = message
        self.details = details
        super().__init__(self.message)


class NotFoundException(DomainError):
    """Запрашиваемый ресурс не найден (→ HTTP 404)."""

    def __init__(self, message="Ресурс не найден", details=""):
        """Создаёт ошибку «не найдено» с сообщением по умолчанию."""
        super().__init__(message=message, details=details)


class ConflictError(DomainError):
    """Конфликт данных, например нарушение уникальности (→ HTTP 409)."""

    def __init__(self, message="Конфликт данных", details=""):
        """Создаёт ошибку конфликта с сообщением по умолчанию."""
        super().__init__(message=message, details=details)


class ValidationError(DomainError):
    """Ошибка доменной валидации входных данных (→ HTTP 422)."""

    def __init__(self, message="Ошибка валидации", details=""):
        """Создаёт ошибку валидации с сообщением по умолчанию."""
        super().__init__(message=message, details=details)


class AuthenticationError(DomainError):
    """Ошибка аутентификации (→ HTTP 401)."""

    def __init__(self, message="Ошибка аутентификации", details=""):
        """Создаёт ошибку аутентификации с сообщением по умолчанию."""
        super().__init__(message=message, details=details)


class PermissionDeniedError(DomainError):
    """Недостаточно прав для операции (→ HTTP 403)."""

    def __init__(self, message="Недостаточно прав", details=""):
        """Создаёт ошибку доступа с сообщением по умолчанию."""
        super().__init__(message=message, details=details)
