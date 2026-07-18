"""Регистрация моделей участников рынка и их профилей в админ-панели."""
from django.contrib import admin

from apps.entities.models import (
    Entity, VendorProfile, SupplierProfile, SystemIntegratorProfile,
    EngineeringCompanyProfile, EngineeringCompanyFunctionCompetency,
    FullCycleVendorProfile, FullCycleFunctionCompetency,
)


@admin.register(Entity)
class EntityAdmin(admin.ModelAdmin):
    """Админ-настройки участника рынка."""
    list_display = ["entity_name", "inn", "entity_type", "is_partner"]
    list_filter = ["entity_type", "is_partner"]
    search_fields = ["entity_name", "inn"]


@admin.register(VendorProfile)
class VendorProfileAdmin(admin.ModelAdmin):
    """Админ-настройки профиля вендора."""
    list_display = ["entity"]
    raw_id_fields = ["entity"]


@admin.register(SupplierProfile)
class SupplierProfileAdmin(admin.ModelAdmin):
    """Админ-настройки профиля поставщика."""
    list_display = ["entity"]
    raw_id_fields = ["entity"]
    filter_horizontal = ["products"]


@admin.register(SystemIntegratorProfile)
class SystemIntegratorProfileAdmin(admin.ModelAdmin):
    """Админ-настройки профиля системного интегратора."""
    list_display = ["entity", "managing_owner"]
    raw_id_fields = ["entity", "managing_owner"]
    filter_horizontal = ["vendor_partners"]


class FunctionCompetencyInline(admin.TabularInline):
    """Инлайн компетенций по функции для профиля инж. компании."""
    model = EngineeringCompanyFunctionCompetency
    extra = 0
    raw_id_fields = ["system_class"]


@admin.register(EngineeringCompanyProfile)
class EngineeringCompanyProfileAdmin(admin.ModelAdmin):
    """Админ-настройки профиля инжиниринговой компании."""
    list_display = ["entity", "region", "resident_object"]
    raw_id_fields = ["entity", "resident_object"]
    filter_horizontal = ["product_competencies"]
    inlines = [FunctionCompetencyInline]


class FullCycleFunctionCompetencyInline(admin.TabularInline):
    """Инлайн компетенций по функции для профиля вендора полного цикла."""
    model = FullCycleFunctionCompetency
    extra = 0
    raw_id_fields = ["system_class"]


@admin.register(FullCycleVendorProfile)
class FullCycleVendorProfileAdmin(admin.ModelAdmin):
    """Админ-настройки профиля вендора полного цикла."""
    list_display = ["entity", "region", "resident_object"]
    raw_id_fields = ["entity", "resident_object"]
    filter_horizontal = ["products"]
    inlines = [FullCycleFunctionCompetencyInline]
