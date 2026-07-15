"""Регистрация модели юридических лиц в админ-панели Django."""
from django.contrib import admin

from apps.owners.models import OwnerEntity


@admin.register(OwnerEntity)
class OwnerEntityAdmin(admin.ModelAdmin):
    """Админ-настройки юр. лица: колонки, фильтры, поиск, read-only is_root."""
    list_display = ["owner_name", "is_root", "owner", "ultimate_owner"]
    list_filter = ["is_root"]
    search_fields = ["owner_name"]
    raw_id_fields = ["owner", "ultimate_owner"]
    readonly_fields = ["is_root"]
