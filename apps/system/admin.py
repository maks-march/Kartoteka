from django.contrib import admin

from apps.system.models import AutomationClass, AutomatedSystem


@admin.register(AutomationClass)
class AutomationClassAdmin(admin.ModelAdmin):
    list_display = ["level", "system_class", "description"]
    list_filter = ["level"]
    search_fields = ["system_class"]


@admin.register(AutomatedSystem)
class AutomatedSystemAdmin(admin.ModelAdmin):
    list_display = ["autosystem_name", "autosystem_short_name", "system_class", "vendor", "version", "system_status", "product_type"]
    list_filter = ["system_class__level", "system_status", "product_type"]
    search_fields = ["autosystem_name", "autosystem_short_name", "article", "version"]
    raw_id_fields = ["system_class", "vendor"]
