"""Сценарии аутентификации: регистрация и вход пользователя."""
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError

from apps.users.repositories.user_repository import UserRepository


class AuthUseCase:
    """Сценарии аутентификации: регистрация и вход пользователя."""
    def __init__(self, user_repo: UserRepository = None):
        """Инициализирует use case, позволяя подменить репозиторий (для тестов)."""
        self.user_repo = user_repo or UserRepository()

    def register(self, username: str, password: str):
        """Регистрирует пользователя, проверяя уникальность и длину пароля."""
        if self.user_repo.get_by_username(username):
            raise ValidationError("Пользователь уже существуте")

        if len(password) < 4:
            raise ValidationError("Пароль слишком короткий")

        return self.user_repo.create(username, password)

    def login(self, username: str, password: str):
        """Проверяет учётные данные и возвращает пользователя."""
        user = authenticate(username=username, password=password)
        if not user:
            raise ValidationError("Неправильный логин или пароль")
        return user
