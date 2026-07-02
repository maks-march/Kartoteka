from django.contrib import admin

from apps.entities.models import Entity


@admin.register(Entity)
class EntityAdmin(admin.ModelAdmin):
    list_display = ["entity_name", "inn", "entity_type", "is_partner"]
    list_filter = ["entity_type", "is_partner"]
    search_fields = ["entity_name", "inn"]
