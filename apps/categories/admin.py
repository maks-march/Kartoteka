"""Регистрация модели категорий в админ-панели Django."""
from django.contrib import admin

from apps.categories.models import Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Админ-настройки категории объекта: колонки, фильтры и поиск."""
    list_display = ["category_name", "object_level"]
    list_filter = ["object_level"]
    search_fields = ["category_name"]
