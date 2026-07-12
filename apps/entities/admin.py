from django.contrib import admin

from apps.entities.models import (
    Entity, VendorProfile, SupplierProfile, SystemIntegratorProfile,
    EngineeringCompanyProfile, FunctionCompetency,
)


@admin.register(Entity)
class EntityAdmin(admin.ModelAdmin):
    list_display = ["entity_name", "inn", "entity_type", "is_partner"]
    list_filter = ["entity_type", "is_partner"]
    search_fields = ["entity_name", "inn"]


@admin.register(VendorProfile)
class VendorProfileAdmin(admin.ModelAdmin):
    list_display = ["entity"]
    raw_id_fields = ["entity"]


@admin.register(SupplierProfile)
class SupplierProfileAdmin(admin.ModelAdmin):
    list_display = ["entity"]
    raw_id_fields = ["entity"]
    filter_horizontal = ["products"]


@admin.register(SystemIntegratorProfile)
class SystemIntegratorProfileAdmin(admin.ModelAdmin):
    list_display = ["entity", "managing_owner"]
    raw_id_fields = ["entity", "managing_owner"]
    filter_horizontal = ["vendor_partners"]


class FunctionCompetencyInline(admin.TabularInline):
    model = FunctionCompetency
    extra = 0
    raw_id_fields = ["system_class"]


@admin.register(EngineeringCompanyProfile)
class EngineeringCompanyProfileAdmin(admin.ModelAdmin):
    list_display = ["entity", "region", "resident_object"]
    raw_id_fields = ["entity", "resident_object"]
    filter_horizontal = ["product_competencies"]
    inlines = [FunctionCompetencyInline]
