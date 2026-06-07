"""Use-case: регистрация нового пользователя."""

from users.domain.entities import UserEntity
from users.repository.protocol import UserRepository
from common.exceptions import ConflictError, ValidationError


class RegisterUserUseCase:
    """
    Регистрация пользователя.
    - Валидация входных данных
    - Проверка на уникальность username/email
    - Хеширование пароля
    - Создание через репозиторий
    """

    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def execute(self, username: str, email: str, password: str) -> UserEntity:
        # --- Валидация ---
        self._validate_input(username, email, password)

        # --- Проверка уникальности ---
        if self.user_repo.exists_by_username(username):
            raise ConflictError(
                message="Пользователь с таким username уже существует",
                details=f"username={username}",
            )

        if self.user_repo.exists_by_email(email):
            raise ConflictError(
                message="Пользователь с таким email уже существует",
                details=f"email={email}",
            )

        # --- Хеширование пароля ---
        hashed_password = self.user_repo.hash_password(password)

        # --- Создание ---
        user = UserEntity(
            username=username,
            email=email,
            password_hash=hashed_password,
        )
        created_user = self.user_repo.create(user)
        return created_user

    @staticmethod
    def _validate_input(username: str, email: str, password: str) -> None:
        errors = []
        if not username or len(username.strip()) < 3:
            errors.append("Username должен содержать минимум 3 символа")
        if not email or "@" not in email:
            errors.append("Некорректный email")
        if not password or len(password) < 8:
            errors.append("Пароль должен содержать минимум 8 символов")
        if errors:
            raise ValidationError(
                message="Ошибка валидации данных",
                details="; ".join(errors),
            )
