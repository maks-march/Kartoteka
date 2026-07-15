"""Репозиторий доступа к данным пользователей."""
from django.contrib.auth.models import User


class UserRepository:
    """Доступ к данным пользователей."""
    def get_by_username(self, username: str) -> User | None:
        """Возвращает пользователя по имени или None."""
        return User.objects.filter(username=username).first()

    def create(self, username: str, password: str) -> User:
        """Создаёт нового пользователя с заданным паролем."""
        return User.objects.create_user(username=username, password=password)
