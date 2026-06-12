class DomainError(Exception):
    def __init__(self, message="", details=""):
        self.message = message
        self.details = details
        super().__init__(self.message)


class NotFoundException(DomainError):
    def __init__(self, message="Ресурс не найден", details=""):
        super().__init__(message=message, details=details)


class ConflictError(DomainError):
    def __init__(self, message="Конфликт данных", details=""):
        super().__init__(message=message, details=details)


class ValidationError(DomainError):
    def __init__(self, message="Ошибка валидации", details=""):
        super().__init__(message=message, details=details)


class AuthenticationError(DomainError):
    def __init__(self, message="Ошибка аутентификации", details=""):
        super().__init__(message=message, details=details)


class PermissionDeniedError(DomainError):
    def __init__(self, message="Недостаточно прав", details=""):
        super().__init__(message=message, details=details)
