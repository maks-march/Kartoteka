"""Конфигурация Django-приложения систем автоматизации."""
from django.apps import AppConfig


class SystemConfig(AppConfig):
    """Конфигурация приложения ``system``."""
    name = 'apps.system'
    label = 'system'
