from django.contrib import admin

from apps.objects.models import Object, ObjectSystem


@admin.register(Object)
class ObjectAdmin(admin.ModelAdmin):
    list_display = ["name", "level", "parent", "category", "owner_entity", "is_deleted", "creator_id", "created_at"]
    list_filter = ["level", "is_deleted", "created_at"]
    search_fields = ["name"]
    raw_id_fields = ["parent", "owner_entity"]


@admin.register(ObjectSystem)
class ObjectSystemAdmin(admin.ModelAdmin):
    list_display = ["object", "system", "status", "implementation_date", "integrator", "implimentor"]
    list_filter = ["status", "implementation_date"]
    raw_id_fields = ["object", "system", "integrator", "implimentor"]
