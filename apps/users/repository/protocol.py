"""Repository-интерфейс для работы с пользователями (абстракция)."""

from abc import ABC, abstractmethod
from typing import Optional

from users.domain.entities import UserEntity


class UserRepository(ABC):
    """
    Контракт репозитория пользователей.
    Реализация должна быть в users/repository/impl.py.
    """

    @abstractmethod
    def create(self, user: UserEntity) -> UserEntity:
        """Создать пользователя."""
        ...

    @abstractmethod
    def get_by_id(self, user_id: int) -> Optional[UserEntity]:
        """Получить пользователя по ID."""
        ...

    @abstractmethod
    def get_by_username(self, username: str) -> Optional[UserEntity]:
        """Получить пользователя по username."""
        ...

    @abstractmethod
    def get_by_email(self, email: str) -> Optional[UserEntity]:
        """Получить пользователя по email."""
        ...

    @abstractmethod
    def exists_by_username(self, username: str) -> bool:
        """Проверить существование пользователя с данным username."""
        ...

    @abstractmethod
    def exists_by_email(self, email: str) -> bool:
        """Проверить существование пользователя с данным email."""
        ...

    @abstractmethod
    def verify_password(self, password: str, password_hash: str) -> bool:
        """Проверить пароль (через хеш)."""
        ...

    @abstractmethod
    def hash_password(self, password: str) -> str:
        """Захешировать пароль."""
        ...
