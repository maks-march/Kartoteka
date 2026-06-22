from django.contrib import admin

from apps.owners.models import OwnerEntity


@admin.register(OwnerEntity)
class OwnerEntityAdmin(admin.ModelAdmin):
    list_display = ["owner_name", "owner", "ultimate_owner"]
    search_fields = ["owner_name"]
    raw_id_fields = ["owner", "ultimate_owner"]
