"""Конфигурация Django-приложения юридических лиц."""
from django.apps import AppConfig


class OwnersConfig(AppConfig):
    """Конфигурация приложения ``owners``."""
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.owners"
    label = "owners"
