from django.contrib import admin
from core.models import Category, Object


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "level")
    list_filter = ("level",)
    search_fields = ("name",)


@admin.register(Object)
class ObjectAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "level", "category")
    list_filter = ("level", "category")
    search_fields = ("name",)
    ordering = ("name",)
