"""Конфигурация Django-приложения категорий объектов."""
from django.apps import AppConfig


class CategoriesConfig(AppConfig):
    """Конфигурация приложения ``categories``."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.categories'
    label = 'categories'
