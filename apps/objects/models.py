from datetime import datetime

from django.contrib.auth.models import User
from django.db import models
from django.core.exceptions import ValidationError
from apps.core.mixins import AuditableMixin
from apps.core.models import SYSTEM_CLASSES


# Модели связанные с object
class ObjectClass(models.Model):
    """Классы объектов (типизация)"""

    name = models.CharField(
        max_length=100,
        verbose_name='Название класса',
    )
    code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Код класса',
    )
    description = models.TextField(
        blank=True,
        verbose_name='Описание',
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='child_classes',
        verbose_name='Родительский класс',
    )

    class Meta:
        verbose_name = 'Класс объекта'
        verbose_name_plural = 'Классы объектов'
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['name']),
            models.Index(fields=['parent']),
        ]

    def __str__(self):
        return self.name

    def get_hierarchy_path(self):
        """Получить иерархический путь класса"""
        path = []
        current = self
        while current:
            path.insert(0, current.name)
            current = current.parent
        return ' → '.join(path)


# ОСНОВНАЯ МОДЕЛЬ - ОБЪЕКТ
class Object(AuditableMixin, models.Model):
    """Основная сущность - промышленные объекты"""

    HIERARCHY_LEVELS = [
        ('LEVEL_1', 'Уровень 1 (Предприятие/НПЗ)'),
        ('LEVEL_2', 'Уровень 2 (Установка/Цех)'),
        ('LEVEL_3', 'Уровень 3 (Агрегат/Блок/Оборудование)'),
    ]

    CATEGORIES = [
        ('MAIN', 'Основное производство'),
        ('AUX', 'Вспомогательное производство (ОЗХ)'),
        ('INFRA', 'Инфраструктура (АБК)'),
        ('PREP', 'Подготовка сырья'),
        ('STORAGE', 'Хранение и логистика'),
    ]

    STATUSES = [
        ('ACTIVE', 'Активный'),
        ('PROJECT', 'В проекте'),
        ('RECONSTRUCTION', 'Реконструкция'),
        ('STOPPED', 'Остановлен'),
    ]

    name = models.CharField(
        max_length=200,
        verbose_name='Наименование',
    )
    short_name = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Короткое название',
        help_text='Например: Г-43-107, АВТ-6',
    )
    hierarchy_level = models.CharField(
        max_length=20,
        choices=HIERARCHY_LEVELS,
        verbose_name='Уровень иерархии',
    )
    object_class = models.ForeignKey(
        ObjectClass,
        on_delete=models.PROTECT,
        related_name='objects_in_class',
        verbose_name='Класс объекта',
    )
    technology = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Технология (АВТ, МТБЭ, каткрекинг и пр.)',
    )
    category = models.CharField(
        max_length=20,
        choices=CATEGORIES,
        verbose_name='Категория',
    )
    start_year = models.IntegerField(
        verbose_name='Год ввода в эксплуатацию',
    )
    capacity = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='Мощность, тыс.тонн/год',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUSES,
        default='ACTIVE',
        verbose_name='Статус',
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='children',
        verbose_name='Родительский объект',
    )
    address = models.ForeignKey(
        'registry.Address',
        on_delete=models.PROTECT,
        verbose_name='Адрес',
    )
    legal_entity = models.ForeignKey(
        'registry.LegalEntity',
        on_delete=models.PROTECT,
        verbose_name='Юридическое лицо',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания',
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления',
    )

    # ПОЛЕ ДЛЯ ОТСЛЕЖИВАНИЯ СОЗДАТЕЛЯ
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Создал',
        related_name='created_objects'
    )

    class Meta:
        verbose_name = 'Объект'
        verbose_name_plural = 'Объекты'
        ordering = ['hierarchy_level', 'name']
        indexes = [
            models.Index(fields=['hierarchy_level']),
            models.Index(fields=['status']),
            models.Index(fields=['object_class']),
            models.Index(fields=['short_name']),
            models.Index(
                fields=['hierarchy_level', 'status'],
                name='obj_level_status_idx',
            ),
            models.Index(
                fields=['parent_id', 'hierarchy_level'],
                name='obj_parent_level_idx',
            ),
            models.Index(
                fields=['legal_entity', 'hierarchy_level'],
                name='obj_legal_level_idx',
            ),
            models.Index(
                fields=['object_class', 'start_year'],
                name='obj_class_year_idx',
            ),
            models.Index(
                fields=['technology'],
                name='obj_technology_idx',
            ),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_hierarchy_level_display()})"

    def clean(self):
        """Валидация объекта"""
        super().clean()

        # Проверка иерархии
        if self.parent and self.parent.hierarchy_level >= self.hierarchy_level:
            raise ValidationError({
                'parent': 'Родительский объект должен быть выше уровнем'
            })

        # Проверка года
        current_year = datetime.now().year
        if self.start_year > current_year + 1:
            raise ValidationError({
                'start_year': 'Год ввода не может быть в будущем'
            })

        # Проверка мощности
        if self.capacity <= 0:
            raise ValidationError({
                'capacity': 'Мощность должна быть положительным числом'
            })

    def get_top_level_parent(self):
        """Возвращает родителя 1-го уровня (самого верхнего в иерархии)"""
        if self.hierarchy_level == 'LEVEL_1':
            return self
        parent = self.parent
        while parent and parent.parent and parent.hierarchy_level != 'LEVEL_1':
            parent = parent.parent
        return parent

    def get_hierarchy_info(self):
        """Возвращает информацию об иерархии"""
        info = {
            'current': self.name,
            'level': self.get_hierarchy_level_display(),
            'parent': None,
            'top_parent': None,
        }
        if self.parent:
            info['parent'] = self.parent.name
            top_parent = self.get_top_level_parent()
            if top_parent != self:
                info['top_parent'] = top_parent.name
        return info

    def get_system_classes(self):
        """Получить классы систем на объекте"""
        classes = self.automated_systems.values_list(
            'system_class',
            flat=True,
        ).distinct()

        result = []
        for cls in classes:
            if cls:
                for choice_code, choice_name in SYSTEM_CLASSES:
                    if choice_code == cls:
                        result.append(choice_name)
                        break
                else:
                    result.append(cls)
        return result

    def get_integrators(self):
        """Получить всех интеграторов объекта"""
        integrators = set()

        for system in self.automated_systems.all():
            if system.integrator:
                integrators.add(system.integrator)

        return list(integrators)

    # МЕТОДЫ ДЛЯ ПРОВЕРКИ ПРАВ
    def can_edit(self, user):
        """Проверка прав на редактирование"""
        if not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        if user.groups.filter(name='Редакторы').exists():
            return True
        return self.created_by == user

    def can_delete(self, user):
        """Проверка прав на удаление"""
        if not user.is_authenticated:
            return False
        return user.is_superuser


class ClassCharacteristic(models.Model):
    """Характеристики классов объектов"""

    object_class = models.ForeignKey(
        ObjectClass,
        on_delete=models.CASCADE,
        related_name='characteristics',
    )
    name = models.CharField(
        max_length=100,
        verbose_name='Название характеристики',
    )
    code = models.CharField(
        max_length=50,
        verbose_name='Код характеристики',
    )
    unit = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Единица измерения',
    )
    description = models.TextField(
        blank=True,
        verbose_name='Описание',
    )
    is_required = models.BooleanField(
        default=False,
        verbose_name='Обязательная',
    )

    class Meta:
        unique_together = ['object_class', 'code']
        verbose_name = 'Характеристика класса'
        verbose_name_plural = 'Характеристики классов'
        indexes = [
            models.Index(fields=['object_class', 'is_required']),
            models.Index(fields=['code']),
        ]

    def __str__(self):
        return f"{self.object_class.name} - {self.name}"


class ClassAutomationRequirement(models.Model):
    """Требования к автоматизации для классов"""

    object_class = models.ForeignKey(
        'ObjectClass',
        on_delete=models.CASCADE,
        related_name='automation_requirements',
    )
    level = models.ForeignKey(
        'automation.AutomationLevel',
        on_delete=models.CASCADE,
    )
    requirement = models.TextField(
        verbose_name='Требование',
    )
    is_mandatory = models.BooleanField(
        default=True,
        verbose_name='Обязательное',
    )
    regulation = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Норматив',
    )

    class Meta:
        unique_together = ['object_class', 'level']
        verbose_name = 'Требование автоматизации класса'
        verbose_name_plural = 'Требования автоматизации классов'
        indexes = [
            models.Index(fields=['object_class', 'is_mandatory']),
            models.Index(fields=['level', 'is_mandatory']),
        ]


class ObjectCharacteristicValue(models.Model):
    """Значения характеристик объектов"""

    object = models.ForeignKey(
        Object,
        on_delete=models.CASCADE,
        related_name='characteristic_values',
    )
    characteristic = models.ForeignKey(
        ClassCharacteristic,
        on_delete=models.CASCADE,
    )
    value = models.CharField(
        max_length=200,
        verbose_name='Значение',
    )
    measurement_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Дата измерения',
    )
    notes = models.TextField(
        blank=True,
        verbose_name='Примечания',
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления',
    )

    class Meta:
        unique_together = ['object', 'characteristic']
        verbose_name = 'Значение характеристики объекта'
        verbose_name_plural = 'Значения характеристик объектов'
        ordering = ['object', 'characteristic']
        indexes = [
            models.Index(fields=['object', 'characteristic']),
            models.Index(fields=['measurement_date']),
            models.Index(fields=['characteristic', 'value']),
        ]

    def __str__(self):
        return f"{self.object.name} - {self.characteristic.name}: {self.value}"
