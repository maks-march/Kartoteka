from django.contrib import admin

from apps.system.models import AutomationClass, AutomatedSystem, VendorProduct


@admin.register(AutomationClass)
class AutomationClassAdmin(admin.ModelAdmin):
    list_display = ["level", "system_class", "name_ru", "is_composite", "includes", "description"]
    list_filter = ["level", "is_composite"]
    search_fields = ["system_class", "name_ru"]
    raw_id_fields = ["includes"]


@admin.register(VendorProduct)
class VendorProductAdmin(admin.ModelAdmin):
    list_display = ["product_name"]
    search_fields = ["product_name"]


@admin.register(AutomatedSystem)
class AutomatedSystemAdmin(admin.ModelAdmin):
    list_display = ["autosystem_name", "autosystem_short_name", "system_class", "product", "system_status"]
    list_filter = ["system_class__level", "system_status"]
    search_fields = ["autosystem_name", "autosystem_short_name"]
    raw_id_fields = ["system_class", "product"]
    filter_horizontal = ["subsystem_classes"]
