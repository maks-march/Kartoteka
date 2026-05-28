from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User, Group
from django.db.models import Count

from .mixins import AuditLog
from apps.automation.models import *
from apps.registry.models import *
from apps.objects.models import *
from apps.participants.models import *



# =============================================================================
# РАСШИРЕННАЯ АДМИНКА ДЛЯ ПОЛЬЗОВАТЕЛЕЙ
# =============================================================================

class CustomUserAdmin(UserAdmin):
    """Расширенный интерфейс для управления пользователями"""

    list_display = UserAdmin.list_display + ('get_groups', 'last_login')
    list_filter = UserAdmin.list_filter + ('groups',)
    search_fields = UserAdmin.search_fields

    def get_groups(self, obj):
        """Отображение групп пользователя"""
        return ", ".join([g.name for g in obj.groups.all()])
    get_groups.short_description = 'Группы'

    # Используем стандартные fieldsets без изменений
    fieldsets = UserAdmin.fieldsets


# Перерегистрируем User с кастомным админом
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


# =============================================================================
# УПРАВЛЕНИЕ ГРУППАМИ
# =============================================================================

# Отменяем стандартную регистрацию Group
admin.site.unregister(Group)

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    """Административный интерфейс для групп"""
    list_display = ('name', 'user_count', 'permission_count')
    search_fields = ('name',)

    def user_count(self, obj):
        """Количество пользователей в группе"""
        return obj.user_set.count()
    user_count.short_description = 'Пользователей'

    def permission_count(self, obj):
        """Количество прав у группы"""
        return obj.permissions.count()
    permission_count.short_description = 'Прав'


# =============================================================================
# БАЗОВЫЕ МОДЕЛИ
# =============================================================================

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    """Административный интерфейс для адресов"""
    list_display = ('country', 'city', 'street', 'house')
    search_fields = ('country', 'city', 'street')
    list_filter = ('country', 'city')


@admin.register(LegalEntity)
class LegalEntityAdmin(admin.ModelAdmin):
    """Административный интерфейс для юридических лиц"""
    list_display = ('name', 'inn', 'owner', 'group')
    search_fields = ('name', 'inn')
    list_filter = ('owner', 'group')


@admin.register(CompanyGroup)
class CompanyGroupAdmin(admin.ModelAdmin):
    """Административный интерфейс для групп компаний"""
    list_display = ('name', 'company_count', 'object_count', 'description_short')
    search_fields = ('name', 'description')

    def company_count(self, obj):
        """Количество компаний в группе"""
        return obj.legalentity_set.count()
    company_count.short_description = 'Компаний'

    def object_count(self, obj):
        """Количество объектов у компаний группы"""
        total = 0
        for company in obj.legalentity_set.all():
            total += company.object_set.count()
        return total
    object_count.short_description = 'Объектов'

    def description_short(self, obj):
        """Краткое описание"""
        if obj.description and len(obj.description) > 50:
            return obj.description[:50] + '...'
        return obj.description or '—'
    description_short.short_description = 'Описание'


@admin.register(ObjectClass)
class ObjectClassAdmin(admin.ModelAdmin):
    """Административный интерфейс для классов объектов"""
    list_display = ('name', 'code', 'parent_link', 'object_count_display')
    list_filter = ('parent',)
    search_fields = ('code', 'name', 'description')
    ordering = ('name',)

    def parent_link(self, obj):
        """Ссылка на родительский класс"""
        if obj.parent:
            return f"{obj.parent.code} - {obj.parent.name}"
        return "—"
    parent_link.short_description = 'Родительский класс'

    def object_count_display(self, obj):
        """Количество объектов в классе"""
        return obj.objects_in_class.count()
    object_count_display.short_description = 'Объектов'

    def get_queryset(self, request):
        """Оптимизация запросов с аннотацией"""
        queryset = super().get_queryset(request)
        return queryset.annotate(objects_count=Count('objects_in_class'))


# =============================================================================
# INLINE КЛАССЫ
# =============================================================================

class ObjectAutomationLevelInline(admin.TabularInline):
    """Inline для уровней автоматизации объекта"""
    model = ObjectAutomationLevel
    extra = 1


class AutomatedSystemInline(admin.TabularInline):
    """Inline для автоматизированных систем"""
    model = AutomatedSystem
    extra = 1
    fields = (
        'name', 'system_class', 'vendor',
        'integrator', 'status', 'installation_date', 'level',
    )
    show_change_link = True

    def get_formset(self, request, obj=None, **kwargs):
        """Настройка formset для inline"""
        formset = super().get_formset(request, obj, **kwargs)

        if 'level' in formset.form.base_fields:
            formset.form.base_fields['level'].required = False

            try:
                from .models import AutomationLevel
                default_level = AutomationLevel.objects.filter(code='L0').first()
                if default_level:
                    formset.form.base_fields['level'].initial = default_level.pk
                    formset.form.base_fields['level'].empty_label = None
            except Exception:
                pass

        return formset

    def save_formset(self, request, form, formset, change):
        """Сохранение formset с проверкой уровня"""
        instances = formset.save(commit=False)

        for instance in instances:
            if not instance.level_id:
                try:
                    from .models import AutomationLevel
                    default_level = AutomationLevel.objects.filter(code='L0').first()
                    if default_level:
                        instance.level = default_level
                except Exception:
                    pass
            instance.save()

        for obj in formset.deleted_objects:
            obj.delete()


class ObjectCharacteristicValueInline(admin.TabularInline):
    """Inline для значений характеристик"""
    model = ObjectCharacteristicValue
    extra = 1
    fields = ('characteristic', 'value', 'measurement_date')


@admin.register(Object)
class ObjectAdmin(admin.ModelAdmin):
    """Административный интерфейс для объектов"""
    list_display = (
        'name', 'short_name', 'hierarchy_level', 'status',
        'legal_entity', 'object_class', 'start_year', 'get_created_by',
    )
    list_filter = ('hierarchy_level', 'status', 'category', 'object_class')
    search_fields = ('name', 'short_name', 'technology', 'object_class__name')
    readonly_fields = ('created_at', 'updated_at', 'created_by')
    inlines = [
        ObjectAutomationLevelInline,
        AutomatedSystemInline,
        ObjectCharacteristicValueInline,
    ]

    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'short_name', 'hierarchy_level', 'object_class', 'status'),
        }),
        ('Технические характеристики', {
            'fields': ('technology', 'category', 'start_year', 'capacity'),
        }),
        ('Структура и связи', {
            'fields': ('parent', 'address', 'legal_entity'),
        }),
        ('Системная информация', {
            'fields': ('created_at', 'updated_at'),
        }),
        ('Владелец', {
            'fields': ('created_by',),
            'classes': ('collapse',),
        }),
    )

    def get_created_by(self, obj):
        """Отображение создателя"""
        if obj.created_by:
            return obj.created_by.username
        return "—"
    get_created_by.short_description = 'Создал'

    def get_queryset(self, request):
        """Оптимизация запросов с создателем"""
        qs = super().get_queryset(request)
        return qs.select_related('created_by')

    def save_model(self, request, obj, form, change):
        """Сохраняем создателя при создании"""
        if not obj.pk:  # Только при создании
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def get_list_filter(self, request):
        """Динамические фильтры в зависимости от прав"""
        filters = ['hierarchy_level', 'status', 'category', 'object_class']
        if request.user.is_superuser:
            filters.append('created_by')
        return filters


# =============================================================================
# УЧАСТНИКИ
# =============================================================================

@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    """Административный интерфейс для участников"""
    list_display = (
        'name', 'participant_type', 'inn',
        'registration_date', 'is_partner', 'get_financial_display', 'get_created_by',
    )
    list_filter = ('participant_type', 'is_partner', 'registration_date')
    search_fields = ('name', 'inn', 'kam_name', 'contact_person', 'profile')
    readonly_fields = ('created_at', 'updated_at', 'created_by')

    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'inn', 'participant_type', 'is_partner'),
        }),
        ('Регистрационные данные', {
            'fields': ('registration_date', 'website'),
        }),
        ('Контактные лица', {
            'fields': ('kam_name', 'kam_phone', 'contact_person', 'contact_phone'),
        }),
        ('Документы и материалы', {
            'fields': ('presentation_url',),
        }),
        ('Финансовая информация', {
            'fields': ('financial_data',),
            'description': (
                'В формате JSON: [{"year": 2023, "revenue": 1500, '
                '"profit": 200, "employees": 50}]'
            ),
        }),
        ('Профиль компании', {
            'fields': ('profile', 'industries'),
        }),
        ('Контакты', {
            'fields': ('contacts',),
        }),
        ('Системная информация', {
            'fields': ('created_at', 'updated_at'),
        }),
        ('Владелец', {
            'fields': ('created_by',),
            'classes': ('collapse',),
        }),
    )

    def get_financial_display(self, obj):
        """Отображение финансовых данных в списке"""
        summary = obj.get_financial_summary()
        if summary and summary['revenue'] is not None:
            return f"{summary['revenue']} млн.руб."
        return "—"
    get_financial_display.short_description = 'Выручка'

    def get_created_by(self, obj):
        """Отображение создателя"""
        if obj.created_by:
            return obj.created_by.username
        return "—"
    get_created_by.short_description = 'Создал'

    def get_queryset(self, request):
        """Оптимизация запросов с создателем"""
        qs = super().get_queryset(request)
        return qs.select_related('created_by')

    def save_model(self, request, obj, form, change):
        """Сохраняем создателя при создании"""
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


# =============================================================================
# АВТОМАТИЗАЦИЯ
# =============================================================================

@admin.register(AutomationLevel)
class AutomationLevelAdmin(admin.ModelAdmin):
    """Административный интерфейс для уровней автоматизации"""
    list_display = ('code', 'name', 'order', 'get_system_classes_display')
    ordering = ('order',)
    search_fields = ('name', 'code', 'description')

    def get_system_classes_display(self, obj):
        """Отображение классов систем уровня"""
        if obj.system_classes and isinstance(obj.system_classes, list):
            display = ', '.join(obj.get_system_classes_display()[:3])
            if len(obj.system_classes) > 3:
                display += '...'
            return display
        return "—"
    get_system_classes_display.short_description = 'Классы систем'


@admin.register(ObjectAutomationLevel)
class ObjectAutomationLevelAdmin(admin.ModelAdmin):
    """Административный интерфейс для связей объект-уровень"""
    list_display = ('object', 'level', 'status', 'implementation_year')
    list_filter = ('level', 'status')
    search_fields = ('object__name', 'level__name')


@admin.register(AutomatedSystem)
class AutomatedSystemAdmin(admin.ModelAdmin):
    """Административный интерфейс для автоматизированных систем"""
    list_display = (
        'name', 'get_system_class_display', 'object', 'vendor',
        'integrator', 'status', 'installation_date', 'get_created_by',
    )
    list_filter = (
        'system_class', 'status', 'level',
        'installation_date', 'vendor', 'integrator',
    )
    search_fields = ('name', 'object__name', 'vendor__name', 'vendor_product__name')
    readonly_fields = ('created_at', 'updated_at', 'created_by')

    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'system_class', 'object', 'level'),
        }),
        ('Участники проекта', {
            'fields': ('vendor', 'vendor_product', 'integrator', 'implementer'),
        }),
        ('Техническая информация', {
            'fields': ('version', 'modules', 'interfaces'),
        }),
        ('Статус и даты', {
            'fields': ('status', 'installation_date', 'notes'),
        }),
        ('Системная информация', {
            'fields': ('created_at', 'updated_at'),
        }),
        ('Владелец', {
            'fields': ('created_by',),
            'classes': ('collapse',),
        }),
    )

    def get_system_class_display(self, obj):
        """Отображение класса системы"""
        return obj.get_system_class_display() if obj.system_class else '—'
    get_system_class_display.short_description = 'Класс системы'

    def get_created_by(self, obj):
        """Отображение создателя"""
        if obj.created_by:
            return obj.created_by.username
        return "—"
    get_created_by.short_description = 'Создал'

    def get_queryset(self, request):
        """Оптимизация запросов с создателем"""
        qs = super().get_queryset(request)
        return qs.select_related('created_by', 'object', 'vendor', 'integrator')

    def get_form(self, request, obj=None, **kwargs):
        """Делаем поле level необязательным"""
        form = super().get_form(request, obj, **kwargs)
        if 'level' in form.base_fields:
            form.base_fields['level'].required = False
        return form

    def save_model(self, request, obj, form, change):
        """Сохраняем создателя при создании"""
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


# =============================================================================
# ВЕНДОРСКИЕ ПРОДУКТЫ
# =============================================================================

@admin.register(VendorProduct)
class VendorProductAdmin(admin.ModelAdmin):
    """Административный интерфейс для вендорских продуктов"""
    list_display = (
        'name', 'code', 'vendor', 'product_type',
        'is_active', 'release_year', 'get_created_by',
    )
    list_filter = ('product_type', 'is_active', 'vendor', 'release_year')
    search_fields = ('name', 'code', 'vendor__name', 'description')
    readonly_fields = ('created_at', 'updated_at', 'created_by')

    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'code', 'vendor', 'product_type', 'version'),
        }),
        ('Описание и характеристики', {
            'fields': ('description', 'technical_specs', 'system_types', 'industries'),
        }),
        ('Жизненный цикл', {
            'fields': ('release_year', 'end_of_support', 'is_active'),
        }),
        ('Системная информация', {
            'fields': ('created_at', 'updated_at'),
        }),
        ('Владелец', {
            'fields': ('created_by',),
            'classes': ('collapse',),
        }),
    )

    def get_created_by(self, obj):
        """Отображение создателя"""
        if obj.created_by:
            return obj.created_by.username
        return "—"
    get_created_by.short_description = 'Создал'

    def get_queryset(self, request):
        """Оптимизация запросов с создателем"""
        qs = super().get_queryset(request)
        return qs.select_related('created_by', 'vendor')

    def save_model(self, request, obj, form, change):
        """Сохраняем создателя при создании"""
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


# =============================================================================
# ХАРАКТЕРИСТИКИ И ТРЕБОВАНИЯ
# =============================================================================

@admin.register(ClassCharacteristic)
class ClassCharacteristicAdmin(admin.ModelAdmin):
    """Административный интерфейс для характеристик классов"""
    list_display = ('name', 'object_class', 'unit', 'is_required')
    list_filter = ('object_class', 'is_required')
    search_fields = ('name', 'description', 'object_class__name')
    ordering = ('object_class', 'name')


@admin.register(ClassAutomationRequirement)
class ClassAutomationRequirementAdmin(admin.ModelAdmin):
    """Административный интерфейс для требований автоматизации"""
    list_display = ('object_class', 'level', 'requirement_short', 'is_mandatory')
    list_filter = ('object_class', 'level', 'is_mandatory')
    search_fields = ('object_class__name', 'requirement', 'regulation')
    ordering = ('object_class', 'level')

    def requirement_short(self, obj):
        """Краткое отображение требования"""
        if len(obj.requirement) > 50:
            return f"{obj.requirement[:50]}..."
        return obj.requirement
    requirement_short.short_description = 'Требование'


@admin.register(ObjectCharacteristicValue)
class ObjectCharacteristicValueAdmin(admin.ModelAdmin):
    """Административный интерфейс для значений характеристик"""
    list_display = ('object', 'characteristic', 'value_short', 'measurement_date', 'updated_at')
    list_filter = ('characteristic__object_class', 'measurement_date')
    search_fields = ('object__name', 'characteristic__name', 'value')
    ordering = ('-updated_at',)

    def value_short(self, obj):
        """Краткое отображение значения"""
        if len(obj.value) > 50:
            return f"{obj.value[:50]}..."
        return obj.value
    value_short.short_description = 'Значение'


# =============================================================================
# ДОПОЛНИТЕЛЬНЫЕ МОДЕЛИ F2
# =============================================================================

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    """Административный интерфейс для проектов"""
    list_display = ('name', 'participant', 'vendor_product', 'object', 'year', 'successful', 'get_created_by')
    list_filter = ('year', 'successful', 'participant')
    search_fields = ('name', 'participant__name', 'object__name', 'description')
    autocomplete_fields = ['participant', 'vendor_product', 'object']
    readonly_fields = ('created_by',)

    def get_created_by(self, obj):
        """Отображение создателя"""
        if obj.created_by:
            return obj.created_by.username
        return "—"
    get_created_by.short_description = 'Создал'

    def save_model(self, request, obj, form, change):
        """Сохраняем создателя при создании"""
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    """Административный интерфейс для сертификатов"""
    list_display = (
        'name', 'participant', 'certificate_type', 'issued_by',
        'issued_date', 'expiry_date', 'get_created_by'
    )
    list_filter = ('certificate_type', 'issued_date', 'participant')
    search_fields = ('name', 'participant__name', 'issued_by')
    autocomplete_fields = ['participant', 'vendor_product']
    readonly_fields = ('created_by',)

    def get_created_by(self, obj):
        """Отображение создателя"""
        if obj.created_by:
            return obj.created_by.username
        return "—"
    get_created_by.short_description = 'Создал'

    def save_model(self, request, obj, form, change):
        """Сохраняем создателя при создании"""
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    """Административный интерфейс для отзывов"""
    list_display = ('participant', 'rating', 'date', 'source', 'get_created_by')
    list_filter = ('rating', 'date', 'participant')
    search_fields = ('participant__name', 'text', 'source')
    autocomplete_fields = ['participant']
    readonly_fields = ('created_by',)

    def get_created_by(self, obj):
        """Отображение создателя"""
        if obj.created_by:
            return obj.created_by.username
        return "—"
    get_created_by.short_description = 'Создал'

    def save_model(self, request, obj, form, change):
        """Сохраняем создателя при создании"""
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(TCOAnalysis)
class TCOAnalysisAdmin(admin.ModelAdmin):
    """Административный интерфейс для TCO анализа"""
    list_display = (
        'participant', 'vendor_product', 'capex', 'opex_per_year',
        'period_years', 'get_created_by'
    )
    list_filter = ('participant', 'period_years')
    search_fields = ('participant__name', 'vendor_product__name', 'notes')
    autocomplete_fields = ['participant', 'vendor_product']
    readonly_fields = ('created_by',)

    def get_created_by(self, obj):
        """Отображение создателя"""
        if obj.created_by:
            return obj.created_by.username
        return "—"
    get_created_by.short_description = 'Создал'

    def save_model(self, request, obj, form, change):
        """Сохраняем создателя при создании"""
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


# =============================================================================
# АУДИТ
# =============================================================================

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Административный интерфейс для просмотра аудита"""

    list_display = ('timestamp', 'user', 'action', 'content_type', 'object_repr')
    list_filter = ('action', 'content_type', 'timestamp')
    search_fields = ('user__username', 'object_repr', 'changes')
    readonly_fields = (
        'timestamp', 'user', 'action', 'content_type',
        'object_id', 'object_repr', 'changes', 'snapshot',
        'user_ip', 'user_agent',
    )

    fieldsets = (
        ('Основная информация', {
            'fields': ('timestamp', 'user', 'action', 'content_type', 'object_repr'),
        }),
        ('Детали изменений', {
            'fields': ('changes', 'snapshot'),
            'classes': ('wide',),
        }),
        ('Техническая информация', {
            'fields': ('user_ip', 'user_agent'),
            'classes': ('collapse',),
        }),
    )

    def has_add_permission(self, request):
        """Запрет на добавление записей вручную"""
        return False

    def has_change_permission(self, request, obj=None):
        """Запрет на изменение записей аудита"""
        return False

    def has_delete_permission(self, request, obj=None):
        """Только суперпользователь может удалять записи аудита"""
        return request.user.is_superuser

    def get_queryset(self, request):
        """Оптимизация запросов"""
        qs = super().get_queryset(request)
        return qs.select_related('user', 'content_type')


# =============================================================================
# НАСТРОЙКИ АДМИН-ПАНЕЛИ
# =============================================================================

admin.site.site_header = "Картотека промышленных объектов F1-F2"
admin.site.site_title = "Картотека F1-F2"
admin.site.index_title = "Администрирование системы"


# =============================================================================
# INLINE ДЛЯ РАСШИРЕННЫХ АДМИНОК
# =============================================================================

class VendorProductInline(admin.TabularInline):
    """Inline для вендорских продуктов"""
    model = VendorProduct
    extra = 1
    fields = ('name', 'code', 'product_type', 'is_active')
    show_change_link = True


class ParticipantAdminExtended(ParticipantAdmin):
    """Расширенный админ для участников с inline продуктами"""
    inlines = [VendorProductInline]


admin.site.unregister(Participant)
admin.site.register(Participant, ParticipantAdminExtended)


class ClassCharacteristicInline(admin.TabularInline):
    """Inline для характеристик класса"""
    model = ClassCharacteristic
    extra = 1
    fields = ('name', 'code', 'unit', 'is_required')


class ClassAutomationRequirementInline(admin.TabularInline):
    """Inline для требований автоматизации класса"""
    model = ClassAutomationRequirement
    extra = 1
    fields = ('level', 'requirement', 'is_mandatory', 'regulation')


class ObjectClassAdminExtended(ObjectClassAdmin):
    """Расширенный админ для классов с inline характеристиками"""
    inlines = [ClassCharacteristicInline, ClassAutomationRequirementInline]


admin.site.unregister(ObjectClass)

