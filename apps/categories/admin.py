from django.contrib import admin

from apps.categories.models import Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "level"]
    list_filter = ["level"]
    search_fields = ["name"]
