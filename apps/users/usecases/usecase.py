from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError

from apps.users.repositories.user_repository import UserRepository


class AuthUseCase:
    def __init__(self, user_repo: UserRepository = None):
        self.user_repo = user_repo or UserRepository()

    def register(self, username: str, password: str):
        if self.user_repo.get_by_username(username):
            raise ValidationError("User already exists")

        if len(password) < 4:
            raise ValidationError("Password too short")

        return self.user_repo.create(username, password)

    def login(self, username: str, password: str):
        user = authenticate(username=username, password=password)
        if not user:
            raise ValidationError("Invalid credentials")
        return user
