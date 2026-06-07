# from datetime import datetime
#
# from django.contrib.auth.models import User
# from django.core.exceptions import ValidationError
# from django.db import models
#
# from .mixins import AuditableMixin
#
# =============================================================================
# КОНСТАНТЫ
# =============================================================================

SYSTEM_CLASSES = [
    ('DCS', 'DCS (Распределённая система управления)'),
    ('HMI', 'HMI (Человеко-машинный интерфейс)'),
    ('ESD', 'ESD (Аварийная система отключения)'),
    ('APC', 'APC (Расширенное управление процессом)'),
    ('FGS', 'FGS (Система контроля пламени и газа)'),
    ('MES', 'MES (Система управления производством)'),
    ('MES+', 'MES+ (Расширенный MES)'),
    ('MOM', 'MOM (Manufacturing Operations Management)'),
    ('APS', 'APS (Advanced Planning and Scheduling)'),
    ('OEE', 'OEE (Overall Equipment Effectiveness)'),
    ('LIMS', 'LIMS (Laboratory Information Management System)'),
    ('WMS', 'WMS (Warehouse Management System)'),
    ('CMMS', 'CMMS (Computerized Maintenance Management System)'),
    ('DT', 'DT (Digital Twin)'),
    ('DRTO', 'DRTO (Dynamic Real-Time Optimization)'),
    ('ERP', 'ERP (Enterprise Resource Planning)'),
    ('PLM', 'PLM (Product Lifecycle Management)'),
    ('CRM', 'CRM (Customer Relationship Management)'),
    ('HRM', 'HRM (Human Resource Management)'),
    ('PDES', 'PDES (Product Data Exchange Specification)'),
    ('SCADA', 'SCADA (Supervisory Control And Data Acquisition)'),
    ('PLC', 'PLC (Programmable Logic Controller)'),
    ('SENSORS', 'Датчики и сенсоры'),
    ('FIELD_DEVICES', 'Полевые устройства'),
]

LEVEL_SYSTEM_CLASSES_MAPPING = {
    'L0': ['FIELD_DEVICES', 'SENSORS'],
    'L1': ['DCS', 'HMI', 'ESD', 'APC', 'FGS'],
    'L2': ['DCS', 'HMI', 'ESD', 'APC', 'FGS'],
    'L3': [
        'MES', 'MES+', 'MOM', 'APS', 'OEE',
        'LIMS', 'WMS', 'CMMS', 'DT', 'DRTO',
    ],
    'L4': ['ERP', 'PLM', 'CRM', 'HRM', 'PDES'],
}
#
#
# # =============================================================================
# # БАЗОВЫЕ МОДЕЛИ
# # =============================================================================
#
# class CompanyGroup(models.Model):
#     """Группа компаний (холдинг)"""
#
#     name = models.CharField(
#         max_length=200,
#         verbose_name='Название группы',
#     )
#     description = models.TextField(
#         blank=True,
#         verbose_name='Описание',
#     )
#
#     class Meta:
#         verbose_name = 'Группа компаний'
#         verbose_name_plural = 'Группы компаний'
#         indexes = [
#             models.Index(fields=['name']),
#         ]
#
#     def __str__(self):
#         return self.name
#
#
# class Address(models.Model):
#     """Адреса объектов с ФИАС/координатами"""
#
#     country = models.CharField(
#         max_length=100,
#         verbose_name='Страна',
#     )
#     region = models.CharField(
#         max_length=100,
#         verbose_name='Регион',
#     )
#     city = models.CharField(
#         max_length=100,
#         verbose_name='Город',
#     )
#     street = models.CharField(
#         max_length=200,
#         verbose_name='Улица',
#     )
#     house = models.CharField(
#         max_length=20,
#         verbose_name='Дом',
#     )
#     fias_code = models.CharField(
#         max_length=36,
#         blank=True,
#         null=True,
#         verbose_name='Код ФИАС',
#     )
#     latitude = models.DecimalField(
#         max_digits=9,
#         decimal_places=6,
#         blank=True,
#         null=True,
#         verbose_name='Широта',
#     )
#     longitude = models.DecimalField(
#         max_digits=9,
#         decimal_places=6,
#         blank=True,
#         null=True,
#         verbose_name='Долгота',
#     )
#
#     class Meta:
#         verbose_name = 'Адрес'
#         verbose_name_plural = 'Адреса'
#         indexes = [
#             models.Index(fields=['country', 'city']),
#             models.Index(fields=['fias_code']),
#         ]
#
#     def __str__(self):
#         return f"{self.country}, {self.city}, {self.street}, {self.house}"
#
#
# class LegalEntity(models.Model):
#     """Юридические лица-владельцы"""
#
#     name = models.CharField(
#         max_length=200,
#         verbose_name='Наименование',
#     )
#     inn = models.CharField(
#         max_length=12,
#         unique=True,
#         verbose_name='ИНН',
#     )
#     owner = models.ForeignKey(
#         'self',
#         on_delete=models.SET_NULL,
#         blank=True,
#         null=True,
#         verbose_name='Собственник',
#     )
#     group = models.ForeignKey(
#         CompanyGroup,
#         on_delete=models.SET_NULL,
#         blank=True,
#         null=True,
#         verbose_name='Группа компаний',
#     )
#
#     class Meta:
#         verbose_name = 'Юридическое лицо'
#         verbose_name_plural = 'Юридические лица'
#         indexes = [
#             models.Index(fields=['name']),
#             models.Index(fields=['inn']),
#             models.Index(fields=['group', 'owner']),
#         ]
#
#     def __str__(self):
#         return self.name
#
#
# class ObjectClass(models.Model):
#     """Классы объектов (типизация)"""
#
#     name = models.CharField(
#         max_length=100,
#         verbose_name='Название класса',
#     )
#     code = models.CharField(
#         max_length=50,
#         unique=True,
#         verbose_name='Код класса',
#     )
#     description = models.TextField(
#         blank=True,
#         verbose_name='Описание',
#     )
#     parent = models.ForeignKey(
#         'self',
#         on_delete=models.CASCADE,
#         blank=True,
#         null=True,
#         related_name='child_classes',
#         verbose_name='Родительский класс',
#     )
#
#     class Meta:
#         verbose_name = 'Класс объекта'
#         verbose_name_plural = 'Классы объектов'
#         indexes = [
#             models.Index(fields=['code']),
#             models.Index(fields=['name']),
#             models.Index(fields=['parent']),
#         ]
#
#     def __str__(self):
#         return self.name
#
#     def get_hierarchy_path(self):
#         """Получить иерархический путь класса"""
#         path = []
#         current = self
#         while current:
#             path.insert(0, current.name)
#             current = current.parent
#         return ' → '.join(path)
#
#
# # =============================================================================
# # ОСНОВНАЯ МОДЕЛЬ - ОБЪЕКТ
# # =============================================================================
#
# class Object(AuditableMixin, models.Model):
#     """Основная сущность - промышленные объекты"""
#
#     HIERARCHY_LEVELS = [
#         ('LEVEL_1', 'Уровень 1 (Предприятие/НПЗ)'),
#         ('LEVEL_2', 'Уровень 2 (Установка/Цех)'),
#         ('LEVEL_3', 'Уровень 3 (Агрегат/Блок/Оборудование)'),
#     ]
#
#     CATEGORIES = [
#         ('MAIN', 'Основное производство'),
#         ('AUX', 'Вспомогательное производство (ОЗХ)'),
#         ('INFRA', 'Инфраструктура (АБК)'),
#         ('PREP', 'Подготовка сырья'),
#         ('STORAGE', 'Хранение и логистика'),
#     ]
#
#     STATUSES = [
#         ('ACTIVE', 'Активный'),
#         ('PROJECT', 'В проекте'),
#         ('RECONSTRUCTION', 'Реконструкция'),
#         ('STOPPED', 'Остановлен'),
#     ]
#
#     name = models.CharField(
#         max_length=200,
#         verbose_name='Наименование',
#     )
#     short_name = models.CharField(
#         max_length=50,
#         blank=True,
#         verbose_name='Короткое название',
#         help_text='Например: Г-43-107, АВТ-6',
#     )
#     hierarchy_level = models.CharField(
#         max_length=20,
#         choices=HIERARCHY_LEVELS,
#         verbose_name='Уровень иерархии',
#     )
#     object_class = models.ForeignKey(
#         ObjectClass,
#         on_delete=models.PROTECT,
#         related_name='objects_in_class',
#         verbose_name='Класс объекта',
#     )
#     technology = models.CharField(
#         max_length=100,
#         blank=True,
#         verbose_name='Технология (АВТ, МТБЭ, каткрекинг и пр.)',
#     )
#     category = models.CharField(
#         max_length=20,
#         choices=CATEGORIES,
#         verbose_name='Категория',
#     )
#     start_year = models.IntegerField(
#         verbose_name='Год ввода в эксплуатацию',
#     )
#     capacity = models.DecimalField(
#         max_digits=12,
#         decimal_places=2,
#         verbose_name='Мощность, тыс.тонн/год',
#     )
#     status = models.CharField(
#         max_length=20,
#         choices=STATUSES,
#         default='ACTIVE',
#         verbose_name='Статус',
#     )
#     parent = models.ForeignKey(
#         'self',
#         on_delete=models.CASCADE,
#         blank=True,
#         null=True,
#         related_name='children',
#         verbose_name='Родительский объект',
#     )
#     address = models.ForeignKey(
#         Address,
#         on_delete=models.PROTECT,
#         verbose_name='Адрес',
#     )
#     legal_entity = models.ForeignKey(
#         LegalEntity,
#         on_delete=models.PROTECT,
#         verbose_name='Юридическое лицо',
#     )
#     created_at = models.DateTimeField(
#         auto_now_add=True,
#         verbose_name='Дата создания',
#     )
#     updated_at = models.DateTimeField(
#         auto_now=True,
#         verbose_name='Дата обновления',
#     )
#
#     # ПОЛЕ ДЛЯ ОТСЛЕЖИВАНИЯ СОЗДАТЕЛЯ
#     created_by = models.ForeignKey(
#         User,
#         on_delete=models.SET_NULL,
#         null=True,
#         blank=True,
#         verbose_name='Создал',
#         related_name='created_objects'
#     )
#
#     class Meta:
#         verbose_name = 'Объект'
#         verbose_name_plural = 'Объекты'
#         ordering = ['hierarchy_level', 'name']
#         indexes = [
#             models.Index(fields=['hierarchy_level']),
#             models.Index(fields=['status']),
#             models.Index(fields=['object_class']),
#             models.Index(fields=['short_name']),
#             models.Index(
#                 fields=['hierarchy_level', 'status'],
#                 name='obj_level_status_idx',
#             ),
#             models.Index(
#                 fields=['parent_id', 'hierarchy_level'],
#                 name='obj_parent_level_idx',
#             ),
#             models.Index(
#                 fields=['legal_entity', 'hierarchy_level'],
#                 name='obj_legal_level_idx',
#             ),
#             models.Index(
#                 fields=['object_class', 'start_year'],
#                 name='obj_class_year_idx',
#             ),
#             models.Index(
#                 fields=['technology'],
#                 name='obj_technology_idx',
#             ),
#         ]
#
#     def __str__(self):
#         return f"{self.name} ({self.get_hierarchy_level_display()})"
#
#     def clean(self):
#         """Валидация объекта"""
#         super().clean()
#
#         # Проверка иерархии
#         if self.parent and self.parent.hierarchy_level >= self.hierarchy_level:
#             raise ValidationError({
#                 'parent': 'Родительский объект должен быть выше уровнем'
#             })
#
#         # Проверка года
#         current_year = datetime.now().year
#         if self.start_year > current_year + 1:
#             raise ValidationError({
#                 'start_year': 'Год ввода не может быть в будущем'
#             })
#
#         # Проверка мощности
#         if self.capacity <= 0:
#             raise ValidationError({
#                 'capacity': 'Мощность должна быть положительным числом'
#             })
#
#     def get_top_level_parent(self):
#         """Возвращает родителя 1-го уровня (самого верхнего в иерархии)"""
#         if self.hierarchy_level == 'LEVEL_1':
#             return self
#         parent = self.parent
#         while parent and parent.parent and parent.hierarchy_level != 'LEVEL_1':
#             parent = parent.parent
#         return parent
#
#     def get_hierarchy_info(self):
#         """Возвращает информацию об иерархии"""
#         info = {
#             'current': self.name,
#             'level': self.get_hierarchy_level_display(),
#             'parent': None,
#             'top_parent': None,
#         }
#         if self.parent:
#             info['parent'] = self.parent.name
#             top_parent = self.get_top_level_parent()
#             if top_parent != self:
#                 info['top_parent'] = top_parent.name
#         return info
#
#     def get_system_classes(self):
#         """Получить классы систем на объекте"""
#         classes = self.automated_systems.values_list(
#             'system_class',
#             flat=True,
#         ).distinct()
#
#         result = []
#         for cls in classes:
#             if cls:
#                 for choice_code, choice_name in SYSTEM_CLASSES:
#                     if choice_code == cls:
#                         result.append(choice_name)
#                         break
#                 else:
#                     result.append(cls)
#         return result
#
#     def get_integrators(self):
#         """Получить всех интеграторов объекта"""
#         integrators = set()
#
#         for system in self.automated_systems.all():
#             if system.integrator:
#                 integrators.add(system.integrator)
#
#         return list(integrators)
#
#     # МЕТОДЫ ДЛЯ ПРОВЕРКИ ПРАВ
#     def can_edit(self, user):
#         """Проверка прав на редактирование"""
#         if not user.is_authenticated:
#             return False
#         if user.is_superuser:
#             return True
#         if user.groups.filter(name='Редакторы').exists():
#             return True
#         return self.created_by == user
#
#     def can_delete(self, user):
#         """Проверка прав на удаление"""
#         if not user.is_authenticated:
#             return False
#         return user.is_superuser
#
#
# # =============================================================================
# # УРОВНИ АВТОМАТИЗАЦИИ
# # =============================================================================
#
# class AutomationLevel(models.Model):
#     """Уровни автоматизации L1-L4"""
#
#     code = models.CharField(
#         max_length=10,
#         unique=True,
#         verbose_name='Код уровня',
#     )
#     name = models.CharField(
#         max_length=100,
#         verbose_name='Название',
#     )
#     description = models.TextField(
#         verbose_name='Описание',
#     )
#     order = models.IntegerField(
#         default=0,
#         verbose_name='Порядок',
#     )
#     system_classes = models.JSONField(
#         default=list,
#         verbose_name='Классы систем уровня',
#     )
#
#     class Meta:
#         verbose_name = 'Уровень автоматизации'
#         verbose_name_plural = 'Уровни автоматизации'
#         ordering = ['order']
#         indexes = [
#             models.Index(fields=['code']),
#             models.Index(fields=['order']),
#         ]
#
#     def __str__(self):
#         return f"{self.code} - {self.name}"
#
#     def save(self, *args, **kwargs):
#         """Автоматически заполняем system_classes при сохранении"""
#         if not self.system_classes and self.code in LEVEL_SYSTEM_CLASSES_MAPPING:
#             self.system_classes = LEVEL_SYSTEM_CLASSES_MAPPING[self.code]
#         super().save(*args, **kwargs)
#
#     def get_system_classes_display(self):
#         """Получить отображаемые названия классов систем"""
#         result = []
#         for cls_code in self.system_classes:
#             for choice_code, choice_name in SYSTEM_CLASSES:
#                 if choice_code == cls_code:
#                     result.append(choice_name)
#                     break
#             else:
#                 result.append(cls_code)
#         return result
#
#
# class ObjectAutomationLevel(models.Model):
#     """Связь объектов с уровнями автоматизации"""
#
#     IMPLEMENTATION_STATUS = [
#         ('PLANNED', 'Запланировано'),
#         ('IN_PROGRESS', 'В реализации'),
#         ('COMPLETED', 'Реализовано'),
#         ('PARTIAL', 'Частично реализовано'),
#     ]
#
#     object = models.ForeignKey(
#         Object,
#         on_delete=models.CASCADE,
#         related_name='automation_levels',
#     )
#     level = models.ForeignKey(
#         AutomationLevel,
#         on_delete=models.CASCADE,
#     )
#     status = models.CharField(
#         max_length=20,
#         choices=IMPLEMENTATION_STATUS,
#         default='PLANNED',
#     )
#     implementation_year = models.IntegerField(
#         null=True,
#         blank=True,
#     )
#     notes = models.TextField(
#         blank=True,
#     )
#
#     class Meta:
#         unique_together = ['object', 'level']
#         verbose_name = 'Уровень автоматизации объекта'
#         verbose_name_plural = 'Уровни автоматизации объектов'
#         indexes = [
#             models.Index(fields=['object', 'status']),
#             models.Index(fields=['level', 'status']),
#             models.Index(fields=['implementation_year']),
#         ]
#
#
# # =============================================================================
# # УЧАСТНИКИ
# # =============================================================================
#
# class Participant(AuditableMixin, models.Model):
#     """Вендоры, внедренцы, интеграторы"""
#
#     PARTICIPANT_TYPES = [
#         ('VENDOR', 'Вендор (разработчик ПО/оборудования)'),
#         ('ENGINEERING', 'Компания интегратор'),
#         ('FULL_CYCLE', 'Вендор полного цикла'),
#         ('SUPPLIER', 'Поставщик (продавец)'),
#     ]
#
#     name = models.CharField(
#         max_length=200,
#         verbose_name='Наименование',
#     )
#     inn = models.CharField(
#         max_length=12,
#         unique=True,
#         verbose_name='ИНН',
#     )
#     participant_type = models.CharField(
#         max_length=20,
#         choices=PARTICIPANT_TYPES,
#         verbose_name='Тип участника',
#     )
#     is_partner = models.BooleanField(
#         default=False,
#         verbose_name='Флаг партнёра',
#     )
#     industries = models.JSONField(
#         default=list,
#         verbose_name='Отрасли',
#     )
#     contacts = models.JSONField(
#         default=dict,
#         verbose_name='Контактная информация',
#     )
#     profile = models.TextField(
#         blank=True,
#         verbose_name='Профиль компании',
#     )
#     registration_date = models.DateField(
#         null=True,
#         blank=True,
#         verbose_name='Дата регистрации',
#     )
#     website = models.URLField(
#         blank=True,
#         verbose_name='Сайт российского представительства',
#     )
#     kam_name = models.CharField(
#         max_length=100,
#         blank=True,
#         verbose_name='Ответственный КАМ (ФИО)',
#     )
#     kam_phone = models.CharField(
#         max_length=20,
#         blank=True,
#         verbose_name='Телефон КАМ',
#     )
#     contact_person = models.CharField(
#         max_length=100,
#         blank=True,
#         verbose_name='Контактное лицо от ЦК ПА',
#     )
#     contact_phone = models.CharField(
#         max_length=20,
#         blank=True,
#         verbose_name='Телефон контакта',
#     )
#     presentation_url = models.URLField(
#         blank=True,
#         verbose_name='Ссылка на презентацию',
#     )
#     financial_data = models.JSONField(
#         default=list,
#         verbose_name='Финансовые показатели',
#         help_text='[{"year": 2023, "revenue": 1500, "profit": 200, "employees": 50}, ...]',
#     )
#     created_at = models.DateTimeField(
#         auto_now_add=True,
#     )
#     updated_at = models.DateTimeField(
#         auto_now=True,
#     )
#
#     # ПОЛЕ ДЛЯ ОТСЛЕЖИВАНИЯ СОЗДАТЕЛЯ
#     created_by = models.ForeignKey(
#         User,
#         on_delete=models.SET_NULL,
#         null=True,
#         blank=True,
#         verbose_name='Создал',
#         related_name='created_participants'
#     )
#
#     class Meta:
#         verbose_name = 'Участник'
#         verbose_name_plural = 'Участники'
#         ordering = ['name']
#         indexes = [
#             models.Index(fields=['name']),
#             models.Index(fields=['inn']),
#             models.Index(fields=['participant_type', 'is_partner']),
#             models.Index(fields=['registration_date']),
#         ]
#
#     def __str__(self):
#         return f"{self.name} ({self.get_participant_type_display()})"
#
#     def clean(self):
#         """Валидация участника"""
#         # Проверка ИНН
#         if self.inn and len(self.inn) not in [10, 12]:
#             raise ValidationError({
#                 'inn': 'ИНН должен содержать 10 или 12 цифр'
#             })
#
#         # Проверка даты регистрации
#         if self.registration_date and self.registration_date > datetime.now().date():
#             raise ValidationError({
#                 'registration_date': 'Дата регистрации не может быть в будущем'
#             })
#
#     def get_system_types(self):
#         """Возвращает типы систем, с которыми работает участник"""
#
#         vendor_systems = self.automated_systems_vendor.values_list(
#             'system_type',
#             flat=True,
#         ).distinct()
#
#         implementer_systems = self.automated_systems_implementer.values_list(
#             'system_type',
#             flat=True,
#         ).distinct()
#
#         all_systems = set(vendor_systems) | set(implementer_systems)
#         return list(all_systems)
#
#     def get_system_classes(self):
#         """Получить все классы систем, с которыми работает участник"""
#         classes = set()
#
#         vendor_classes = self.automated_systems_vendor.values_list(
#             'system_class',
#             flat=True,
#         ).distinct()
#
#         integrator_classes = self.automated_systems_integrator.values_list(
#             'system_class',
#             flat=True,
#         ).distinct()
#
#         all_classes = set(vendor_classes) | set(integrator_classes)
#         result = []
#         for cls in all_classes:
#             if cls:
#                 for choice_code, choice_name in SYSTEM_CLASSES:
#                     if choice_code == cls:
#                         result.append(choice_name)
#                         break
#                 else:
#                     result.append(cls)
#         return result
#
#     def get_unique_clients(self):
#         """Возвращает количество уникальных заказчиков (юрлиц)"""
#
#         vendor_clients = self.automated_systems_vendor.values(
#             'object__legal_entity',
#         ).distinct().count()
#
#         implementer_clients = self.automated_systems_implementer.values(
#             'object__legal_entity',
#         ).distinct().count()
#
#         return vendor_clients + implementer_clients
#
#     def get_experience_info(self):
#         """Возвращает информацию об опыте с заказчиками"""
#         experience = []
#
#         vendor_systems = self.automated_systems_vendor.select_related(
#             'object__legal_entity',
#         ).all()
#
#         implementer_systems = self.automated_systems_implementer.select_related(
#             'object__legal_entity',
#         ).all()
#
#         all_systems = list(vendor_systems) + list(implementer_systems)
#
#         clients_dict = {}
#         for system in all_systems:
#             if system.object and system.object.legal_entity:
#                 client_id = system.object.legal_entity.id
#                 if client_id not in clients_dict:
#                     clients_dict[client_id] = {
#                         'client': system.object.legal_entity,
#                         'objects': set(),
#                         'systems': set(),
#                         'system_types': set(),
#                     }
#
#                 clients_dict[client_id]['objects'].add(system.object.name)
#                 clients_dict[client_id]['systems'].add(system.name)
#                 clients_dict[client_id]['system_types'].add(system.system_type)
#
#         for client_data in clients_dict.values():
#             experience.append({
#                 'client': client_data['client'],
#                 'objects': list(client_data['objects'])[:3],
#                 'systems': list(client_data['systems'])[:3],
#                 'system_types': list(client_data['system_types']),
#             })
#
#         return experience
#
#     def get_financial_summary(self):
#         """Сводка финансовых данных"""
#         if not self.financial_data:
#             return None
#
#         if not isinstance(self.financial_data, list):
#             return None
#
#         sorted_data = sorted(
#             [d for d in self.financial_data if isinstance(d, dict) and 'year' in d],
#             key=lambda x: x['year'],
#             reverse=True,
#         )
#
#         if not sorted_data:
#             return None
#
#         latest_year = sorted_data[0]
#
#         return {
#             'latest_year': latest_year.get('year'),
#             'revenue': latest_year.get('revenue'),
#             'profit': latest_year.get('profit'),
#             'employees': latest_year.get('employees'),
#             'all_years': sorted_data,
#             'has_data': len(sorted_data) > 0,
#         }
#
#     @staticmethod
#     def get_system_class_display(code):
#         """Получить отображаемое название класса системы"""
#         for choice_code, choice_name in SYSTEM_CLASSES:
#             if choice_code == code:
#                 return choice_name
#         return code
#
#     # МЕТОДЫ ДЛЯ ПРОВЕРКИ ПРАВ
#     def can_edit(self, user):
#         """Проверка прав на редактирование"""
#         if not user.is_authenticated:
#             return False
#         if user.is_superuser:
#             return True
#         if user.groups.filter(name='Редакторы').exists():
#             return True
#         return self.created_by == user
#
#     def can_delete(self, user):
#         """Проверка прав на удаление"""
#         if not user.is_authenticated:
#             return False
#         return user.is_superuser
#
#
# # =============================================================================
# # ВЕНДОРСКИЕ ПРОДУКТЫ
# # =============================================================================
#
# class VendorProduct(AuditableMixin, models.Model):
#     """Вендорский продукт (ранее Технология)"""
#
#     PRODUCT_TYPE_CHOICES = [
#         ('SOFTWARE', 'Программное обеспечение'),
#         ('HARDWARE', 'Аппаратное обеспечение'),
#         ('SERVICE', 'Услуга/Сервис'),
#         ('PLATFORM', 'Платформа'),
#         ('SOLUTION', 'Комплексное решение'),
#         ('CONSULTING', 'Консалтинг'),
#         ('MAINTENANCE', 'Техническое обслуживание'),
#     ]
#
#     name = models.CharField(
#         max_length=200,
#         verbose_name='Название продукта',
#     )
#     vendor = models.ForeignKey(
#         Participant,
#         on_delete=models.PROTECT,
#         related_name='vendor_products',
#         verbose_name='Вендор',
#     )
#     product_type = models.CharField(
#         max_length=20,
#         choices=PRODUCT_TYPE_CHOICES,
#         verbose_name='Тип продукта',
#     )
#     code = models.CharField(
#         max_length=50,
#         unique=True,
#         verbose_name='Артикул/Код',
#     )
#     description = models.TextField(
#         verbose_name='Описание продукта',
#     )
#     version = models.CharField(
#         max_length=50,
#         blank=True,
#         verbose_name='Версия',
#     )
#     system_types = models.JSONField(
#         default=list,
#         verbose_name='Типы систем',
#     )
#     industries = models.JSONField(
#         default=list,
#         verbose_name='Отрасли применения',
#     )
#     technical_specs = models.JSONField(
#         default=dict,
#         verbose_name='Технические характеристики',
#     )
#     release_year = models.IntegerField(
#         null=True,
#         blank=True,
#         verbose_name='Год выпуска',
#     )
#     end_of_support = models.DateField(
#         null=True,
#         blank=True,
#         verbose_name='Конец поддержки',
#     )
#     is_active = models.BooleanField(
#         default=True,
#         verbose_name='Активный продукт',
#     )
#     created_at = models.DateTimeField(
#         auto_now_add=True,
#     )
#     updated_at = models.DateTimeField(
#         auto_now=True,
#     )
#
#     #  ПОЛЕ ДЛЯ ОТСЛЕЖИВАНИЯ СОЗДАТЕЛЯ
#     created_by = models.ForeignKey(
#         User,
#         on_delete=models.SET_NULL,
#         null=True,
#         blank=True,
#         verbose_name='Создал',
#         related_name='created_products'
#     )
#
#     class Meta:
#         verbose_name = 'Вендорский продукт'
#         verbose_name_plural = 'Вендорские продукты'
#         ordering = ['vendor__name', 'name']
#         indexes = [
#             models.Index(fields=['name']),
#             models.Index(fields=['code']),
#             models.Index(fields=['vendor', 'product_type']),
#             models.Index(fields=['release_year']),
#             models.Index(fields=['is_active']),
#         ]
#
#     def __str__(self):
#         return f"{self.name} ({self.vendor.name})"
#
#     def get_implementation_count(self):
#         """Количество внедрений этого продукта"""
#         return self.automated_systems.count()
#
#     def get_clients(self):
#         """Клиенты, использующие этот продукт"""
#         return LegalEntity.objects.filter(
#             object__automated_systems__vendor_product=self,
#         ).distinct()
#
#     # МЕТОДЫ ДЛЯ ПРОВЕРКИ ПРАВ
#     def can_edit(self, user):
#         """Проверка прав на редактирование"""
#         if not user.is_authenticated:
#             return False
#         if user.is_superuser:
#             return True
#         if user.groups.filter(name='Редакторы').exists():
#             return True
#         return self.created_by == user
#
#     def can_delete(self, user):
#         """Проверка прав на удаление"""
#         if not user.is_authenticated:
#             return False
#         return user.is_superuser
#
#
# # =============================================================================
# # АВТОМАТИЗИРОВАННЫЕ СИСТЕМЫ
# # =============================================================================
#
# class AutomatedSystem(AuditableMixin, models.Model):
#     """АСУТП, MES, SCADA системы"""
#
#     STATUS_CHOICES = [
#         ('ACTIVE', 'Активна'),
#         ('INACTIVE', 'Неактивна'),
#         ('MAINTENANCE', 'На обслуживании'),
#         ('UPGRADE', 'На модернизации'),
#     ]
#
#     name = models.CharField(
#         max_length=200,
#         verbose_name='Название системы',
#     )
#     system_class = models.CharField(
#         max_length=50,
#         choices=SYSTEM_CLASSES,
#         blank=True,
#         verbose_name='Класс системы',
#     )
#     object = models.ForeignKey(
#         Object,
#         on_delete=models.CASCADE,
#         related_name='automated_systems',
#     )
#     level = models.ForeignKey(
#         AutomationLevel,
#         on_delete=models.PROTECT,
#         verbose_name='Уровень автоматизации',
#         null=True,
#         blank=True,
#     )
#     vendor = models.ForeignKey(
#         Participant,
#         on_delete=models.PROTECT,
#         related_name='automated_systems_vendor',
#         verbose_name='Вендор',
#     )
#     integrator = models.ForeignKey(
#         Participant,
#         on_delete=models.SET_NULL,
#         null=True,
#         blank=True,
#         related_name='automated_systems_integrator',
#         verbose_name='Интегратор (Инжиниринговая компания)',
#     )
#     vendor_product = models.ForeignKey(
#         VendorProduct,
#         on_delete=models.SET_NULL,
#         null=True,
#         blank=True,
#         related_name='automated_systems',
#         verbose_name='Вендорский продукт',
#     )
#     created_at = models.DateTimeField(
#         auto_now_add=True,
#         verbose_name='Дата создания',
#     )
#     updated_at = models.DateTimeField(
#         auto_now=True,
#         verbose_name='Дата обновления',
#     )
#     implementer = models.ForeignKey(
#         Participant,
#         on_delete=models.PROTECT,
#         related_name='automated_systems_implementer',
#         null=True,
#         blank=True,
#         verbose_name='Внедряющая компания',
#     )
#     version = models.CharField(
#         max_length=50,
#         blank=True,
#         verbose_name='Версия',
#     )
#     modules = models.JSONField(
#         default=list,
#         verbose_name='Модули системы',
#     )
#     interfaces = models.JSONField(
#         default=list,
#         verbose_name='Интерфейсы',
#     )
#     status = models.CharField(
#         max_length=20,
#         choices=STATUS_CHOICES,
#         default='ACTIVE',
#         verbose_name='Статус',
#     )
#     installation_date = models.DateField(
#         null=True,
#         blank=True,
#         verbose_name='Дата установки',
#     )
#     notes = models.TextField(
#         blank=True,
#         verbose_name='Примечания',
#     )
#
#     # ПОЛЕ ДЛЯ ОТСЛЕЖИВАНИЯ СОЗДАТЕЛЯ
#     created_by = models.ForeignKey(
#         User,
#         on_delete=models.SET_NULL,
#         null=True,
#         blank=True,
#         verbose_name='Создал',
#         related_name='created_systems'
#     )
#
#     class Meta:
#         verbose_name = 'Автоматизированная система'
#         verbose_name_plural = 'Автоматизированные системы'
#         indexes = [
#             models.Index(fields=['name']),
#             models.Index(fields=['system_class']),
#             models.Index(fields=['status']),
#             models.Index(fields=['installation_date']),
#             models.Index(fields=['object', 'system_class']),
#             models.Index(fields=['vendor', 'status']),
#             models.Index(fields=['level', 'status']),
#             models.Index(
#                 fields=['object_id', 'vendor_id'],
#                 name='sys_object_vendor_idx',
#             ),
#             models.Index(
#                 fields=['object_id', 'integrator_id'],
#                 name='sys_object_integrator_idx',
#             ),
#             models.Index(
#                 fields=['vendor_product', 'status'],
#                 name='sys_product_status_idx',
#             ),
#         ]
#
#     def __str__(self):
#         return f"{self.name} ({self.get_system_class_display()}) на {self.object.name}"
#
#     def clean(self):
#         """Валидация системы"""
#         # Проверка совместимости уровня и класса
#         if self.level and self.system_class:
#             level_classes = LEVEL_SYSTEM_CLASSES_MAPPING.get(self.level.code, [])
#             if self.system_class not in level_classes:
#                 raise ValidationError({
#                     'system_class': f'Класс {self.system_class} не соответствует уровню {self.level.code}'
#                 })
#
#         # Проверка статуса
#         if self.status == 'UPGRADE' and not self.notes:
#             raise ValidationError({
#                 'notes': 'При статусе "На модернизации" необходимо указать примечания'
#             })
#
#     def get_system_class_display(self):
#         """Получить отображаемое название класса системы"""
#         if not self.system_class:
#             return "—"
#         for choice_code, choice_name in SYSTEM_CLASSES:
#             if choice_code == self.system_class:
#                 return choice_name
#         return self.system_class
#
#     # МЕТОДЫ ДЛЯ ПРОВЕРКИ ПРАВ
#     def can_edit(self, user):
#         """Проверка прав на редактирование"""
#         if not user.is_authenticated:
#             return False
#         if user.is_superuser:
#             return True
#         if user.groups.filter(name='Редакторы').exists():
#             return True
#         return self.created_by == user
#
#     def can_delete(self, user):
#         """Проверка прав на удаление"""
#         if not user.is_authenticated:
#             return False
#         return user.is_superuser
#
#
# # =============================================================================
# # ХАРАКТЕРИСТИКИ И ТРЕБОВАНИЯ
# # =============================================================================
#
# class ClassCharacteristic(models.Model):
#     """Характеристики классов объектов"""
#
#     object_class = models.ForeignKey(
#         ObjectClass,
#         on_delete=models.CASCADE,
#         related_name='characteristics',
#     )
#     name = models.CharField(
#         max_length=100,
#         verbose_name='Название характеристики',
#     )
#     code = models.CharField(
#         max_length=50,
#         verbose_name='Код характеристики',
#     )
#     unit = models.CharField(
#         max_length=20,
#         blank=True,
#         verbose_name='Единица измерения',
#     )
#     description = models.TextField(
#         blank=True,
#         verbose_name='Описание',
#     )
#     is_required = models.BooleanField(
#         default=False,
#         verbose_name='Обязательная',
#     )
#
#     class Meta:
#         unique_together = ['object_class', 'code']
#         verbose_name = 'Характеристика класса'
#         verbose_name_plural = 'Характеристики классов'
#         indexes = [
#             models.Index(fields=['object_class', 'is_required']),
#             models.Index(fields=['code']),
#         ]
#
#     def __str__(self):
#         return f"{self.object_class.name} - {self.name}"
#
#
# class ClassAutomationRequirement(models.Model):
#     """Требования к автоматизации для классов"""
#
#     object_class = models.ForeignKey(
#         ObjectClass,
#         on_delete=models.CASCADE,
#         related_name='automation_requirements',
#     )
#     level = models.ForeignKey(
#         AutomationLevel,
#         on_delete=models.CASCADE,
#     )
#     requirement = models.TextField(
#         verbose_name='Требование',
#     )
#     is_mandatory = models.BooleanField(
#         default=True,
#         verbose_name='Обязательное',
#     )
#     regulation = models.CharField(
#         max_length=200,
#         blank=True,
#         verbose_name='Норматив',
#     )
#
#     class Meta:
#         unique_together = ['object_class', 'level']
#         verbose_name = 'Требование автоматизации класса'
#         verbose_name_plural = 'Требования автоматизации классов'
#         indexes = [
#             models.Index(fields=['object_class', 'is_mandatory']),
#             models.Index(fields=['level', 'is_mandatory']),
#         ]
#
#
# class ObjectCharacteristicValue(models.Model):
#     """Значения характеристик объектов"""
#
#     object = models.ForeignKey(
#         Object,
#         on_delete=models.CASCADE,
#         related_name='characteristic_values',
#     )
#     characteristic = models.ForeignKey(
#         ClassCharacteristic,
#         on_delete=models.CASCADE,
#     )
#     value = models.CharField(
#         max_length=200,
#         verbose_name='Значение',
#     )
#     measurement_date = models.DateField(
#         null=True,
#         blank=True,
#         verbose_name='Дата измерения',
#     )
#     notes = models.TextField(
#         blank=True,
#         verbose_name='Примечания',
#     )
#     updated_at = models.DateTimeField(
#         auto_now=True,
#         verbose_name='Дата обновления',
#     )
#
#     class Meta:
#         unique_together = ['object', 'characteristic']
#         verbose_name = 'Значение характеристики объекта'
#         verbose_name_plural = 'Значения характеристик объектов'
#         ordering = ['object', 'characteristic']
#         indexes = [
#             models.Index(fields=['object', 'characteristic']),
#             models.Index(fields=['measurement_date']),
#             models.Index(fields=['characteristic', 'value']),
#         ]
#
#     def __str__(self):
#         return f"{self.object.name} - {self.characteristic.name}: {self.value}"
#
#
# # =============================================================================
# # ДОПОЛНИТЕЛЬНЫЕ МОДЕЛИ F2
# # =============================================================================
#
# class Project(AuditableMixin, models.Model):
#     """Проекты внедрения участника"""
#
#     participant = models.ForeignKey(
#         'Participant',
#         on_delete=models.CASCADE,
#         related_name='projects',
#         verbose_name='Участник',
#     )
#     vendor_product = models.ForeignKey(
#         'VendorProduct',
#         on_delete=models.SET_NULL,
#         null=True,
#         blank=True,
#         related_name='projects',
#         verbose_name='Вендорский продукт',
#     )
#     object = models.ForeignKey(
#         'Object',
#         on_delete=models.CASCADE,
#         related_name='projects',
#         verbose_name='Объект внедрения',
#     )
#     name = models.CharField(
#         max_length=200,
#         verbose_name='Название проекта',
#     )
#     year = models.IntegerField(
#         verbose_name='Год реализации',
#     )
#     successful = models.BooleanField(
#         default=True,
#         verbose_name='Успешный пуск',
#     )
#     description = models.TextField(
#         blank=True,
#         verbose_name='Описание',
#     )
#     created_at = models.DateTimeField(
#         auto_now_add=True,
#     )
#     updated_at = models.DateTimeField(
#         auto_now=True,
#     )
#
#     # ПОЛЕ ДЛЯ ОТСЛЕЖИВАНИЯ СОЗДАТЕЛЯ
#     created_by = models.ForeignKey(
#         User,
#         on_delete=models.SET_NULL,
#         null=True,
#         blank=True,
#         verbose_name='Создал',
#         related_name='created_projects'
#     )
#
#     class Meta:
#         verbose_name = 'Проект'
#         verbose_name_plural = 'Проекты'
#         ordering = ['-year']
#         indexes = [
#             models.Index(
#                 fields=['participant', 'year'],
#                 name='project_participant_year_idx',
#             ),
#             models.Index(
#                 fields=['object', 'year'],
#                 name='project_object_year_idx',
#             ),
#         ]
#
#     def __str__(self):
#         return f"{self.name} ({self.year})"
#
#     # МЕТОДЫ ДЛЯ ПРОВЕРКИ ПРАВ
#     def can_edit(self, user):
#         """Проверка прав на редактирование"""
#         if not user.is_authenticated:
#             return False
#         if user.is_superuser:
#             return True
#         if user.groups.filter(name='Редакторы').exists():
#             return True
#         return self.created_by == user
#
#
# class Certificate(AuditableMixin, models.Model):
#     """Сертификаты участника"""
#
#     CERTIFICATE_TYPES = [
#         ('ISO', 'Сертификат ISO'),
#         ('AUTHORIZED', 'Авторизация вендора'),
#         ('SPECIALIST', 'Сертифицированный специалист'),
#         ('OTHER', 'Другое'),
#     ]
#
#     participant = models.ForeignKey(
#         'Participant',
#         on_delete=models.CASCADE,
#         related_name='certificates',
#         verbose_name='Участник',
#     )
#     vendor_product = models.ForeignKey(
#         'VendorProduct',
#         on_delete=models.SET_NULL,
#         null=True,
#         blank=True,
#         related_name='certificates',
#         verbose_name='Вендорский продукт',
#     )
#     name = models.CharField(
#         max_length=200,
#         verbose_name='Название сертификата',
#     )
#     certificate_type = models.CharField(
#         max_length=20,
#         choices=CERTIFICATE_TYPES,
#         verbose_name='Тип сертификата',
#     )
#     issued_by = models.CharField(
#         max_length=200,
#         verbose_name='Кем выдан',
#     )
#     issued_date = models.DateField(
#         verbose_name='Дата выдачи',
#     )
#     expiry_date = models.DateField(
#         null=True,
#         blank=True,
#         verbose_name='Срок действия',
#     )
#     file = models.FileField(
#         upload_to='certificates/',
#         null=True,
#         blank=True,
#         verbose_name='Файл сертификата',
#     )
#     created_at = models.DateTimeField(
#         auto_now_add=True,
#     )
#     updated_at = models.DateTimeField(
#         auto_now=True,
#     )
#
#     # ПОЛЕ ДЛЯ ОТСЛЕЖИВАНИЯ СОЗДАТЕЛЯ
#     created_by = models.ForeignKey(
#         User,
#         on_delete=models.SET_NULL,
#         null=True,
#         blank=True,
#         verbose_name='Создал',
#         related_name='created_certificates'
#     )
#
#     class Meta:
#         verbose_name = 'Сертификат'
#         verbose_name_plural = 'Сертификаты'
#         ordering = ['-issued_date']
#         indexes = [
#             models.Index(
#                 fields=['participant', 'certificate_type'],
#                 name='cert_participant_type_idx',
#             ),
#             models.Index(
#                 fields=['expiry_date'],
#                 name='cert_expiry_date_idx',
#             ),
#         ]
#
#     def __str__(self):
#         return f"{self.name} ({self.get_certificate_type_display()})"
#
#
# class Review(AuditableMixin, models.Model):
#     """Отзывы о участнике"""
#
#     RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]
#
#     participant = models.ForeignKey(
#         'Participant',
#         on_delete=models.CASCADE,
#         related_name='reviews',
#         verbose_name='Участник',
#     )
#     text = models.TextField(
#         verbose_name='Текст отзыва',
#     )
#     rating = models.IntegerField(
#         choices=RATING_CHOICES,
#         verbose_name='Оценка',
#     )
#     date = models.DateField(
#         verbose_name='Дата отзыва',
#     )
#     source = models.CharField(
#         max_length=200,
#         blank=True,
#         verbose_name='Источник',
#     )
#     created_at = models.DateTimeField(
#         auto_now_add=True,
#     )
#     updated_at = models.DateTimeField(
#         auto_now=True,
#     )
#
#     # ПОЛЕ ДЛЯ ОТСЛЕЖИВАНИЯ СОЗДАТЕЛЯ
#     created_by = models.ForeignKey(
#         User,
#         on_delete=models.SET_NULL,
#         null=True,
#         blank=True,
#         verbose_name='Создал',
#         related_name='created_reviews'
#     )
#
#     class Meta:
#         verbose_name = 'Отзыв'
#         verbose_name_plural = 'Отзывы'
#         ordering = ['-date']
#         indexes = [
#             models.Index(
#                 fields=['participant', 'rating'],
#                 name='review_participant_rating_idx',
#             ),
#         ]
#
#     def __str__(self):
#         return f"Отзыв о {self.participant.name} ({self.rating}★)"
#
#
# class TCOAnalysis(AuditableMixin, models.Model):
#     """TCO анализ для продуктов"""
#
#     participant = models.ForeignKey(
#         'Participant',
#         on_delete=models.CASCADE,
#         related_name='tco_analyses',
#         verbose_name='Участник',
#     )
#     vendor_product = models.ForeignKey(
#         'VendorProduct',
#         on_delete=models.CASCADE,
#         related_name='tco_analyses',
#         verbose_name='Вендорский продукт',
#     )
#     capex = models.DecimalField(
#         max_digits=15,
#         decimal_places=2,
#         verbose_name='CAPEX (млн руб)',
#     )
#     opex_per_year = models.DecimalField(
#         max_digits=15,
#         decimal_places=2,
#         verbose_name='OPEX в год (млн руб)',
#     )
#     period_years = models.IntegerField(
#         default=5,
#         verbose_name='Период анализа (лет)',
#     )
#     discount_rate = models.DecimalField(
#         max_digits=5,
#         decimal_places=2,
#         default=10.0,
#         verbose_name='Ставка дисконтирования %',
#     )
#     notes = models.TextField(
#         blank=True,
#         verbose_name='Примечания',
#     )
#     created_at = models.DateTimeField(
#         auto_now_add=True,
#     )
#     updated_at = models.DateTimeField(
#         auto_now=True,
#     )
#
#     # ПОЛЕ ДЛЯ ОТСЛЕЖИВАНИЯ СОЗДАТЕЛЯ
#     created_by = models.ForeignKey(
#         User,
#         on_delete=models.SET_NULL,
#         null=True,
#         blank=True,
#         verbose_name='Создал',
#         related_name='created_tco'
#     )
#
#     class Meta:
#         verbose_name = 'TCO анализ'
#         verbose_name_plural = 'TCO анализы'
#         indexes = [
#             models.Index(
#                 fields=['participant', 'vendor_product'],
#                 name='tco_participant_product_idx',
#             ),
#         ]
#
#     def __str__(self):
#         return f"TCO: {self.vendor_product.name} ({self.participant.name})"
#
#     def total_tco(self):
#         """Расчет общей стоимости владения"""
#         total = float(self.capex)
#         for year in range(1, self.period_years + 1):
#             discount = 1 / ((1 + float(self.discount_rate) / 100) ** year)
#             total += float(self.opex_per_year) * discount
#         return round(total, 2)
