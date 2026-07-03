from django.contrib import admin

from apps.owners.models import OwnerEntity


@admin.register(OwnerEntity)
class OwnerEntityAdmin(admin.ModelAdmin):
    list_display = ["owner_name", "is_root", "owner", "ultimate_owner"]
    list_filter = ["is_root"]
    search_fields = ["owner_name"]
    raw_id_fields = ["owner", "ultimate_owner"]
    readonly_fields = ["is_root"]
