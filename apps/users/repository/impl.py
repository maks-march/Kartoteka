"""Django ORM-реализация репозитория пользователей."""

from django.contrib.auth import authenticate
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth import get_user_model

from users.domain.entities import UserEntity
from users.repository.protocol import UserRepository

User = get_user_model()


class DjangoUserRepository(UserRepository):
    """Реализация UserRepository через Django ORM."""

    def create(self, user: UserEntity) -> UserEntity:
        db_user = User.objects.create_user(
            username=user.username,
            email=user.email,
            password=user.password_hash,  # уже захеширован
            is_active=user.is_active,
        )
        return UserEntity(
            id=db_user.pk,
            username=db_user.username,
            email=db_user.email,
            is_active=db_user.is_active,
            is_staff=db_user.is_staff,
            created_at=db_user.date_joined,
            updated_at=db_user.last_login,
        )

    def get_by_id(self, user_id: int) -> UserEntity | None:
        db_user = User.objects.filter(pk=user_id).first()
        if not db_user:
            return None
        return UserEntity(
            id=db_user.pk,
            username=db_user.username,
            email=db_user.email,
            is_active=db_user.is_active,
            is_staff=db_user.is_staff,
            created_at=db_user.date_joined,
            updated_at=db_user.last_login,
        )

    def get_by_username(self, username: str) -> UserEntity | None:
        db_user = User.objects.filter(username=username).first()
        if not db_user:
            return None
        return UserEntity(
            id=db_user.pk,
            username=db_user.username,
            email=db_user.email,
            is_active=db_user.is_active,
            is_staff=db_user.is_staff,
            created_at=db_user.date_joined,
            updated_at=db_user.last_login,
        )

    def get_by_email(self, email: str) -> UserEntity | None:
        db_user = User.objects.filter(email=email).first()
        if not db_user:
            return None
        return UserEntity(
            id=db_user.pk,
            username=db_user.username,
            email=db_user.email,
            is_active=db_user.is_active,
            is_staff=db_user.is_staff,
            created_at=db_user.date_joined,
            updated_at=db_user.last_login,
        )

    def exists_by_username(self, username: str) -> bool:
        return User.objects.filter(username=username).exists()

    def exists_by_email(self, email: str) -> bool:
        return User.objects.filter(email=email).exists()

    def verify_password(self, password: str, password_hash: str) -> bool:
        """Проверить пароль через Django's check_password."""
        return check_password(password, password_hash)

    def hash_password(self, password: str) -> str:
        """Захешировать пароль через Django's make_password (PBKDF2)."""
        return make_password(password)

    def authenticate(self, username: str, password: str) -> UserEntity | None:
        """Аутентифицировать пользователя."""
        user = authenticate(username=username, password=password)
        if not user:
            return None
        return UserEntity(
            id=user.pk,
            username=user.username,
            email=user.email,
            is_active=user.is_active,
            is_staff=user.is_staff,
            created_at=user.date_joined,
            updated_at=user.last_login,
        )
