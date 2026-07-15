"""Конфигурация корневого (общего) Django-приложения."""
from django.apps import AppConfig


class CoreConfig(AppConfig):
    """Конфигурация приложения ``core`` (главная страница-хаб и утилиты)."""

    name = 'apps.core'
    label = 'core'
