from django.contrib.auth.models import User


class UserRepository:
    def get_by_username(self, username: str) -> User | None:
        return User.objects.filter(username=username).first()

    def create(self, username: str, password: str) -> User:
        return User.objects.create_user(username=username, password=password)
