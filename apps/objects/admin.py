"""Регистрация моделей объектов в админ-панели Django."""
from django.contrib import admin

from apps.objects.models import Object, ObjectSystem


@admin.register(Object)
class ObjectAdmin(admin.ModelAdmin):
    """Админ-настройки объекта производства: колонки, фильтры и поиск."""

    list_display = ["object_name", "object_class", "hierarchy_level", "parent_object", "category", "owner_entity", "status", "city", "created_at"]
    list_filter = ["hierarchy_level", "status", "is_reconstructed", "created_at"]
    search_fields = ["object_name", "object_short_name", "object_law_name", "city", "title"]
    raw_id_fields = ["parent_object", "owner_entity"]


@admin.register(ObjectSystem)
class ObjectSystemAdmin(admin.ModelAdmin):
    """Админ-настройки связи «система на объекте»."""

    list_display = ["object", "system", "status", "implementation_date", "implementor"]
    list_filter = ["status", "implementation_date"]
    raw_id_fields = ["object", "system", "implementor"]
