"""Use-case: аутентификация пользователя."""

from typing import Dict, Any

from users.domain.entities import UserEntity
from users.repository.impl import DjangoUserRepository
from common.exceptions import AuthenticationError


class AuthenticateUserUseCase:
    """
    Аутентификация пользователя.
    Возвращает токен при успешном входе.
    """

    def __init__(self, user_repo: DjangoUserRepository):
        self.user_repo = user_repo

    def execute(self, username: str, password: str) -> Dict[str, Any]:
        user = self.user_repo.authenticate(username=username, password=password)

        if user is None:
            raise AuthenticationError(
                message="Неверный username или пароль",
            )

        if not user.is_active:
            raise AuthenticationError(
                message="Пользователь неактивен",
            )

        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_staff": user.is_staff,
        }
