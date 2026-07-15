"""Конфигурация Django-приложения участников рынка."""
from django.apps import AppConfig


class EntitiesConfig(AppConfig):
    """Конфигурация приложения ``entities``."""
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.entities"
    label = "entities"
