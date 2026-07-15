"""Конфигурация Django-приложения пользователей."""
from django.apps import AppConfig


class UsersConfig(AppConfig):
    """Конфигурация приложения ``users``."""
    name = 'apps.users'
    label = 'users'
