from django.contrib.auth.models import User
from django.db import models

from old_apps.core.mixins import AuditableMixin
from django.core.exceptions import ValidationError
from old_apps.core.models import LEVEL_SYSTEM_CLASSES_MAPPING, SYSTEM_CLASSES


# Субъекты системы автоматизации
class AutomationLevel(models.Model):
    """Уровни автоматизации L1-L4"""
    code = models.CharField(
        max_length=10,
        unique=True,
        verbose_name='Код уровня',
    )
    name = models.CharField(
        max_length=100,
        verbose_name='Название',
    )
    description = models.TextField(
        verbose_name='Описание',
    )
    order = models.IntegerField(
        default=0,
        verbose_name='Порядок',
    )
    system_classes = models.JSONField(
        default=list,
        verbose_name='Классы систем уровня',
    )

    class Meta:
        verbose_name = 'Уровень автоматизации'
        verbose_name_plural = 'Уровни автоматизации'
        ordering = ['order']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['order']),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"

    def save(self, *args, **kwargs):
        """Автоматически заполняем system_classes при сохранении"""
        if not self.system_classes and self.code in LEVEL_SYSTEM_CLASSES_MAPPING:
            self.system_classes = LEVEL_SYSTEM_CLASSES_MAPPING[self.code]
        super().save(*args, **kwargs)

    def get_system_classes_display(self):
        """Получить отображаемые названия классов систем"""
        result = []
        for cls_code in self.system_classes:
            for choice_code, choice_name in SYSTEM_CLASSES:
                if choice_code == cls_code:
                    result.append(choice_name)
                    break
            else:
                result.append(cls_code)
        return result

class ObjectAutomationLevel(models.Model):
    """Связь объектов с уровнями автоматизации"""

    IMPLEMENTATION_STATUS = [
        ('PLANNED', 'Запланировано'),
        ('IN_PROGRESS', 'В реализации'),
        ('COMPLETED', 'Реализовано'),
        ('PARTIAL', 'Частично реализовано'),
    ]

    object = models.ForeignKey(
        'objects.Object',
        on_delete=models.CASCADE,
        related_name='automation_levels',
    )
    level = models.ForeignKey(
        AutomationLevel,
        on_delete=models.CASCADE,
    )
    status = models.CharField(
        max_length=20,
        choices=IMPLEMENTATION_STATUS,
        default='PLANNED',
    )
    implementation_year = models.IntegerField(
        null=True,
        blank=True,
    )
    notes = models.TextField(
        blank=True,
    )

    class Meta:
        unique_together = ['object', 'level']
        verbose_name = 'Уровень автоматизации объекта'
        verbose_name_plural = 'Уровни автоматизации объектов'
        indexes = [
            models.Index(fields=['object', 'status']),
            models.Index(fields=['level', 'status']),
            models.Index(fields=['implementation_year']),
        ]

class AutomatedSystem(AuditableMixin, models.Model):
    """АСУТП, MES, SCADA системы"""

    STATUS_CHOICES = [
        ('ACTIVE', 'Активна'),
        ('INACTIVE', 'Неактивна'),
        ('MAINTENANCE', 'На обслуживании'),
        ('UPGRADE', 'На модернизации'),
    ]

    name = models.CharField(
        max_length=200,
        verbose_name='Название системы',
    )
    system_class = models.CharField(
        max_length=50,
        choices=SYSTEM_CLASSES,
        blank=True,
        verbose_name='Класс системы',
    )
    object = models.ForeignKey(
        'objects.Object',
        on_delete=models.CASCADE,
        related_name='automated_systems',
    )
    level = models.ForeignKey(
        AutomationLevel,
        on_delete=models.PROTECT,
        verbose_name='Уровень автоматизации',
        null=True,
        blank=True,
    )
    vendor = models.ForeignKey(
        'participants.Participant',
        on_delete=models.PROTECT,
        related_name='automated_systems_vendor',
        verbose_name='Вендор',
    )
    integrator = models.ForeignKey(
        'participants.Participant',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='automated_systems_integrator',
        verbose_name='Интегратор (Инжиниринговая компания)',
    )
    vendor_product = models.ForeignKey(
        'participants.VendorProduct',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='automated_systems',
        verbose_name='Вендорский продукт',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания',
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления',
    )
    implementer = models.ForeignKey(
        'participants.Participant',
        on_delete=models.PROTECT,
        related_name='automated_systems_implementer',
        null=True,
        blank=True,
        verbose_name='Внедряющая компания',
    )
    version = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Версия',
    )
    modules = models.JSONField(
        default=list,
        verbose_name='Модули системы',
    )
    interfaces = models.JSONField(
        default=list,
        verbose_name='Интерфейсы',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='ACTIVE',
        verbose_name='Статус',
    )
    installation_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Дата установки',
    )
    notes = models.TextField(
        blank=True,
        verbose_name='Примечания',
    )

    # ПОЛЕ ДЛЯ ОТСЛЕЖИВАНИЯ СОЗДАТЕЛЯ
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Создал',
        related_name='created_systems'
    )

    class Meta:
        verbose_name = 'Автоматизированная система'
        verbose_name_plural = 'Автоматизированные системы'
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['system_class']),
            models.Index(fields=['status']),
            models.Index(fields=['installation_date']),
            models.Index(fields=['object', 'system_class']),
            models.Index(fields=['vendor', 'status']),
            models.Index(fields=['level', 'status']),
            models.Index(
                fields=['object_id', 'vendor_id'],
                name='sys_object_vendor_idx',
            ),
            models.Index(
                fields=['object_id', 'integrator_id'],
                name='sys_object_integrator_idx',
            ),
            models.Index(
                fields=['vendor_product', 'status'],
                name='sys_product_status_idx',
            ),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_system_class_display()}) на {self.object.name}"

    def clean(self):
        """Валидация системы"""
        # Проверка совместимости уровня и класса
        if self.level and self.system_class:
            level_classes = LEVEL_SYSTEM_CLASSES_MAPPING.get(self.level.code, [])
            if self.system_class not in level_classes:
                raise ValidationError({
                    'system_class': f'Класс {self.system_class} не соответствует уровню {self.level.code}'
                })

        # Проверка статуса
        if self.status == 'UPGRADE' and not self.notes:
            raise ValidationError({
                'notes': 'При статусе "На модернизации" необходимо указать примечания'
            })

    def get_system_class_display(self):
        """Получить отображаемое название класса системы"""
        if not self.system_class:
            return "—"
        for choice_code, choice_name in SYSTEM_CLASSES:
            if choice_code == self.system_class:
                return choice_name
        return self.system_class

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
