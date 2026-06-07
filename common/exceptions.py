"""Кастомные исключения для domain-слоя."""


class DomainError(Exception):
    """Базовое исключение для доменных ошибок."""

    def __init__(self, message: str = "", details: str = ""):
        self.message = message
        self.details = details
        super().__init__(self.message)


class NotFoundException(DomainError):
    def __init__(self, message: str = "Ресурс не найден", details: str = ""):
        super().__init__(message=message, details=details)


class ConflictError(DomainError):
    def __init__(self, message: str = "Конфликт данных", details: str = ""):
        super().__init__(message=message, details=details)


class ValidationError(DomainError):
    def __init__(self, message: str = "Ошибка валидации", details: str = ""):
        super().__init__(message=message, details=details)


class AuthenticationError(DomainError):
    def __init__(self, message: str = "Ошибка аутентификации", details: str = ""):
        super().__init__(message=message, details=details)


class PermissionDeniedError(DomainError):
    def __init__(self, message: str = "Недостаточно прав", details: str = ""):
        super().__init__(message=message, details=details)
