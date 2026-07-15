"""Конфигурация Django-приложения объектов производства."""
from django.apps import AppConfig


class ObjectsConfig(AppConfig):
    """Конфигурация приложения ``objects``."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.objects"
    label = "objects"
