import datetime

from django.contrib.auth.models import User
from django.db import models

from django.core.exceptions import ValidationError
from apps.core.mixins import AuditableMixin
from apps.core.models import SYSTEM_CLASSES


# Участники рынка
class Participant(AuditableMixin, models.Model):
    """Вендоры, внедренцы, интеграторы"""

    PARTICIPANT_TYPES = [
        ('VENDOR', 'Вендор (разработчик ПО/оборудования)'),
        ('ENGINEERING', 'Компания интегратор'),
        ('FULL_CYCLE', 'Вендор полного цикла'),
        ('SUPPLIER', 'Поставщик (продавец)'),
    ]

    name = models.CharField(
        max_length=200,
        verbose_name='Наименование',
    )
    inn = models.CharField(
        max_length=12,
        unique=True,
        verbose_name='ИНН',
    )
    participant_type = models.CharField(
        max_length=20,
        choices=PARTICIPANT_TYPES,
        verbose_name='Тип участника',
    )
    is_partner = models.BooleanField(
        default=False,
        verbose_name='Флаг партнёра',
    )
    industries = models.JSONField(
        default=list,
        verbose_name='Отрасли',
    )
    contacts = models.JSONField(
        default=dict,
        verbose_name='Контактная информация',
    )
    profile = models.TextField(
        blank=True,
        verbose_name='Профиль компании',
    )
    registration_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Дата регистрации',
    )
    website = models.URLField(
        blank=True,
        verbose_name='Сайт российского представительства',
    )
    kam_name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Ответственный КАМ (ФИО)',
    )
    kam_phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Телефон КАМ',
    )
    contact_person = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Контактное лицо от ЦК ПА',
    )
    contact_phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Телефон контакта',
    )
    presentation_url = models.URLField(
        blank=True,
        verbose_name='Ссылка на презентацию',
    )
    financial_data = models.JSONField(
        default=list,
        verbose_name='Финансовые показатели',
        help_text='[{"year": 2023, "revenue": 1500, "profit": 200, "employees": 50}, ...]',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        auto_now=True,
    )

    # ПОЛЕ ДЛЯ ОТСЛЕЖИВАНИЯ СОЗДАТЕЛЯ
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Создал',
        related_name='created_participants'
    )

    class Meta:
        verbose_name = 'Участник'
        verbose_name_plural = 'Участники'
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['inn']),
            models.Index(fields=['participant_type', 'is_partner']),
            models.Index(fields=['registration_date']),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_participant_type_display()})"

    def clean(self):
        """Валидация участника"""
        # Проверка ИНН
        if self.inn and len(self.inn) not in [10, 12]:
            raise ValidationError({
                'inn': 'ИНН должен содержать 10 или 12 цифр'
            })

        # Проверка даты регистрации
        if self.registration_date and self.registration_date > datetime.now().date():
            raise ValidationError({
                'registration_date': 'Дата регистрации не может быть в будущем'
            })

    def get_system_types(self):
        """Возвращает типы систем, с которыми работает участник"""

        vendor_systems = self.automated_systems_vendor.values_list(
            'system_type',
            flat=True,
        ).distinct()

        implementer_systems = self.automated_systems_implementer.values_list(
            'system_type',
            flat=True,
        ).distinct()

        all_systems = set(vendor_systems) | set(implementer_systems)
        return list(all_systems)

    def get_system_classes(self):
        """Получить все классы систем, с которыми работает участник"""
        classes = set()

        vendor_classes = self.automated_systems_vendor.values_list(
            'system_class',
            flat=True,
        ).distinct()

        integrator_classes = self.automated_systems_integrator.values_list(
            'system_class',
            flat=True,
        ).distinct()

        all_classes = set(vendor_classes) | set(integrator_classes)
        result = []
        for cls in all_classes:
            if cls:
                for choice_code, choice_name in SYSTEM_CLASSES:
                    if choice_code == cls:
                        result.append(choice_name)
                        break
                else:
                    result.append(cls)
        return result

    def get_unique_clients(self):
        """Возвращает количество уникальных заказчиков (юрлиц)"""

        vendor_clients = self.automated_systems_vendor.values(
            'object__legal_entity',
        ).distinct().count()

        implementer_clients = self.automated_systems_implementer.values(
            'object__legal_entity',
        ).distinct().count()

        return vendor_clients + implementer_clients

    def get_experience_info(self):
        """Возвращает информацию об опыте с заказчиками"""
        experience = []

        vendor_systems = self.automated_systems_vendor.select_related(
            'object__legal_entity',
        ).all()

        implementer_systems = self.automated_systems_implementer.select_related(
            'object__legal_entity',
        ).all()

        all_systems = list(vendor_systems) + list(implementer_systems)

        clients_dict = {}
        for system in all_systems:
            if system.object and system.object.legal_entity:
                client_id = system.object.legal_entity.id
                if client_id not in clients_dict:
                    clients_dict[client_id] = {
                        'client': system.object.legal_entity,
                        'object': set(),
                        'systems': set(),
                        'system_types': set(),
                    }

                clients_dict[client_id]['object'].add(system.object.name)
                clients_dict[client_id]['systems'].add(system.name)
                clients_dict[client_id]['system_types'].add(system.system_type)

        for client_data in clients_dict.values():
            experience.append({
                'client': client_data['client'],
                'object': list(client_data['object'])[:3],
                'systems': list(client_data['systems'])[:3],
                'system_types': list(client_data['system_types']),
            })

        return experience

    def get_financial_summary(self):
        """Сводка финансовых данных"""
        if not self.financial_data:
            return None

        if not isinstance(self.financial_data, list):
            return None

        sorted_data = sorted(
            [d for d in self.financial_data if isinstance(d, dict) and 'year' in d],
            key=lambda x: x['year'],
            reverse=True,
        )

        if not sorted_data:
            return None

        latest_year = sorted_data[0]

        return {
            'latest_year': latest_year.get('year'),
            'revenue': latest_year.get('revenue'),
            'profit': latest_year.get('profit'),
            'employees': latest_year.get('employees'),
            'all_years': sorted_data,
            'has_data': len(sorted_data) > 0,
        }

    @staticmethod
    def get_system_class_display(code):
        """Получить отображаемое название класса системы"""
        for choice_code, choice_name in SYSTEM_CLASSES:
            if choice_code == code:
                return choice_name
        return code

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

# Продукт - АСУТП
class VendorProduct(AuditableMixin, models.Model):
    """Вендорский продукт (ранее Технология)"""

    PRODUCT_TYPE_CHOICES = [
        ('SOFTWARE', 'Программное обеспечение'),
        ('HARDWARE', 'Аппаратное обеспечение'),
        ('SERVICE', 'Услуга/Сервис'),
        ('PLATFORM', 'Платформа'),
        ('SOLUTION', 'Комплексное решение'),
        ('CONSULTING', 'Консалтинг'),
        ('MAINTENANCE', 'Техническое обслуживание'),
    ]

    name = models.CharField(
        max_length=200,
        verbose_name='Название продукта',
    )
    vendor = models.ForeignKey(
        Participant,
        on_delete=models.PROTECT,
        related_name='vendor_products',
        verbose_name='Вендор',
    )
    product_type = models.CharField(
        max_length=20,
        choices=PRODUCT_TYPE_CHOICES,
        verbose_name='Тип продукта',
    )
    code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Артикул/Код',
    )
    description = models.TextField(
        verbose_name='Описание продукта',
    )
    version = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Версия',
    )
    system_types = models.JSONField(
        default=list,
        verbose_name='Типы систем',
    )
    industries = models.JSONField(
        default=list,
        verbose_name='Отрасли применения',
    )
    technical_specs = models.JSONField(
        default=dict,
        verbose_name='Технические характеристики',
    )
    release_year = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='Год выпуска',
    )
    end_of_support = models.DateField(
        null=True,
        blank=True,
        verbose_name='Конец поддержки',
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Активный продукт',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        auto_now=True,
    )

    #  ПОЛЕ ДЛЯ ОТСЛЕЖИВАНИЯ СОЗДАТЕЛЯ
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Создал',
        related_name='created_products'
    )

    class Meta:
        verbose_name = 'Вендорский продукт'
        verbose_name_plural = 'Вендорские продукты'
        ordering = ['vendor__name', 'name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['code']),
            models.Index(fields=['vendor', 'product_type']),
            models.Index(fields=['release_year']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.name} ({self.vendor.name})"

    def get_implementation_count(self):
        """Количество внедрений этого продукта"""
        return self.automated_systems.count()

    def get_clients(self):
        """Клиенты, использующие этот продукт"""
        return LegalEntity.objects.filter(
            object__automated_systems__vendor_product=self,
        ).distinct()

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


class Project(AuditableMixin, models.Model):
    """Проекты внедрения участника"""

    participant = models.ForeignKey(
        'participants.Participant',
        on_delete=models.CASCADE,
        related_name='projects',
        verbose_name='Участник',
    )
    vendor_product = models.ForeignKey(
        'participants.VendorProduct',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='projects',
        verbose_name='Вендорский продукт',
    )
    object = models.ForeignKey(
        'objects.Object',
        on_delete=models.CASCADE,
        related_name='projects',
        verbose_name='Объект внедрения',
    )
    name = models.CharField(
        max_length=200,
        verbose_name='Название проекта',
    )
    year = models.IntegerField(
        verbose_name='Год реализации',
    )
    successful = models.BooleanField(
        default=True,
        verbose_name='Успешный пуск',
    )
    description = models.TextField(
        blank=True,
        verbose_name='Описание',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        auto_now=True,
    )

    # ПОЛЕ ДЛЯ ОТСЛЕЖИВАНИЯ СОЗДАТЕЛЯ
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Создал',
        related_name='created_projects'
    )

    class Meta:
        verbose_name = 'Проект'
        verbose_name_plural = 'Проекты'
        ordering = ['-year']
        indexes = [
            models.Index(
                fields=['participant', 'year'],
                name='project_participant_year_idx',
            ),
            models.Index(
                fields=['object', 'year'],
                name='project_object_year_idx',
            ),
        ]

    def __str__(self):
        return f"{self.name} ({self.year})"

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


class Certificate(AuditableMixin, models.Model):
    """Сертификаты участника"""

    CERTIFICATE_TYPES = [
        ('ISO', 'Сертификат ISO'),
        ('AUTHORIZED', 'Авторизация вендора'),
        ('SPECIALIST', 'Сертифицированный специалист'),
        ('OTHER', 'Другое'),
    ]

    participant = models.ForeignKey(
        'Participant',
        on_delete=models.CASCADE,
        related_name='certificates',
        verbose_name='Участник',
    )
    vendor_product = models.ForeignKey(
        'VendorProduct',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='certificates',
        verbose_name='Вендорский продукт',
    )
    name = models.CharField(
        max_length=200,
        verbose_name='Название сертификата',
    )
    certificate_type = models.CharField(
        max_length=20,
        choices=CERTIFICATE_TYPES,
        verbose_name='Тип сертификата',
    )
    issued_by = models.CharField(
        max_length=200,
        verbose_name='Кем выдан',
    )
    issued_date = models.DateField(
        verbose_name='Дата выдачи',
    )
    expiry_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Срок действия',
    )
    file = models.FileField(
        upload_to='certificates/',
        null=True,
        blank=True,
        verbose_name='Файл сертификата',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        auto_now=True,
    )

    # ПОЛЕ ДЛЯ ОТСЛЕЖИВАНИЯ СОЗДАТЕЛЯ
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Создал',
        related_name='created_certificates'
    )

    class Meta:
        verbose_name = 'Сертификат'
        verbose_name_plural = 'Сертификаты'
        ordering = ['-issued_date']
        indexes = [
            models.Index(
                fields=['participant', 'certificate_type'],
                name='cert_participant_type_idx',
            ),
            models.Index(
                fields=['expiry_date'],
                name='cert_expiry_date_idx',
            ),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_certificate_type_display()})"


class Review(AuditableMixin, models.Model):
    """Отзывы о участнике"""

    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]

    participant = models.ForeignKey(
        'participants.Participant',
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='Участник',
    )
    text = models.TextField(
        verbose_name='Текст отзыва',
    )
    rating = models.IntegerField(
        choices=RATING_CHOICES,
        verbose_name='Оценка',
    )
    date = models.DateField(
        verbose_name='Дата отзыва',
    )
    source = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Источник',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        auto_now=True,
    )

    # ПОЛЕ ДЛЯ ОТСЛЕЖИВАНИЯ СОЗДАТЕЛЯ
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Создал',
        related_name='created_reviews'
    )

    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        ordering = ['-date']
        indexes = [
            models.Index(
                fields=['participant', 'rating'],
                name='review_participant_rating_idx',
            ),
        ]

    def __str__(self):
        return f"Отзыв о {self.participant.name} ({self.rating}★)"


class TCOAnalysis(AuditableMixin, models.Model):
    """TCO анализ для продуктов"""

    participant = models.ForeignKey(
        'participants.Participant',
        on_delete=models.CASCADE,
        related_name='tco_analyses',
        verbose_name='Участник',
    )
    vendor_product = models.ForeignKey(
        'participants.VendorProduct',
        on_delete=models.CASCADE,
        related_name='tco_analyses',
        verbose_name='Вендорский продукт',
    )
    capex = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name='CAPEX (млн руб)',
    )
    opex_per_year = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name='OPEX в год (млн руб)',
    )
    period_years = models.IntegerField(
        default=5,
        verbose_name='Период анализа (лет)',
    )
    discount_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=10.0,
        verbose_name='Ставка дисконтирования %',
    )
    notes = models.TextField(
        blank=True,
        verbose_name='Примечания',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        auto_now=True,
    )

    # ПОЛЕ ДЛЯ ОТСЛЕЖИВАНИЯ СОЗДАТЕЛЯ
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Создал',
        related_name='created_tco'
    )

    class Meta:
        verbose_name = 'TCO анализ'
        verbose_name_plural = 'TCO анализы'
        indexes = [
            models.Index(
                fields=['participant', 'vendor_product'],
                name='tco_participant_product_idx',
            ),
        ]

    def __str__(self):
        return f"TCO: {self.vendor_product.name} ({self.participant.name})"

    def total_tco(self):
        """Расчет общей стоимости владения"""
        total = float(self.capex)
        for year in range(1, self.period_years + 1):
            discount = 1 / ((1 + float(self.discount_rate) / 100) ** year)
            total += float(self.opex_per_year) * discount
        return round(total, 2)
