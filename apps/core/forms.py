# core/forms.py
from django import forms

from apps.automation.models import *
from apps.objects.models import *
from apps.participants.models import *


class ObjectForm(forms.ModelForm):
    """Форма для создания и редактирования объектов"""

    class Meta:
        model = Object
        fields = [
            'name', 'short_name', 'hierarchy_level', 'object_class',
            'technology', 'category', 'start_year', 'capacity',
            'status', 'parent', 'address', 'legal_entity'
        ]
        widgets = {
            'start_year': forms.NumberInput(attrs={'min': 1900, 'max': 2100}),
            'capacity': forms.NumberInput(attrs={'step': '0.01'}),
        }
        labels = {
            'name': 'Наименование',
            'short_name': 'Короткое название',
            'hierarchy_level': 'Уровень иерархии',
            'object_class': 'Класс объекта',
            'technology': 'Технология',
            'category': 'Категория',
            'start_year': 'Год ввода',
            'capacity': 'Мощность (тыс.тонн/год)',
            'status': 'Статус',
            'parent': 'Родительский объект',
            'address': 'Адрес',
            'legal_entity': 'Юридическое лицо',
        }
        help_texts = {
            'short_name': 'Например: Г-43-107, АВТ-6',
            'capacity': 'В тысячах тонн в год',
        }


class ParticipantForm(forms.ModelForm):
    """Форма для создания и редактирования участников"""

    class Meta:
        model = Participant
        fields = [
            'name', 'inn', 'participant_type', 'is_partner',
            'industries', 'profile', 'registration_date', 'website',
            'kam_name', 'kam_phone', 'contact_person', 'contact_phone',
            'presentation_url', 'financial_data', 'contacts'
        ]
        widgets = {
            'registration_date': forms.DateInput(attrs={'type': 'date'}),
            'industries': forms.Textarea(attrs={'rows': 3}),
            'financial_data': forms.Textarea(attrs={'rows': 5, 'class': 'font-monospace'}),
            'contacts': forms.Textarea(attrs={'rows': 5, 'class': 'font-monospace'}),
        }
        labels = {
            'name': 'Наименование',
            'inn': 'ИНН',
            'participant_type': 'Тип участника',
            'is_partner': 'Партнёр',
            'industries': 'Отрасли',
            'profile': 'Профиль компании',
            'registration_date': 'Дата регистрации',
            'website': 'Сайт',
            'kam_name': 'Ответственный КАМ',
            'kam_phone': 'Телефон КАМ',
            'contact_person': 'Контактное лицо',
            'contact_phone': 'Телефон контакта',
            'presentation_url': 'Ссылка на презентацию',
            'financial_data': 'Финансовые показатели',
            'contacts': 'Дополнительные контакты',
        }


class AutomatedSystemForm(forms.ModelForm):
    """Форма для создания и редактирования автоматизированных систем"""

    class Meta:
        model = AutomatedSystem
        fields = [
            'name', 'system_class', 'object', 'level',
            'vendor', 'integrator', 'vendor_product',
            'version', 'modules', 'interfaces',
            'status', 'installation_date', 'notes'
        ]
        widgets = {
            'installation_date': forms.DateInput(attrs={'type': 'date'}),
            'modules': forms.Textarea(attrs={'rows': 3}),
            'interfaces': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 4}),
        }
        labels = {
            'name': 'Название системы',
            'system_class': 'Класс системы',
            'object': 'Объект',
            'level': 'Уровень автоматизации',
            'vendor': 'Вендор',
            'integrator': 'Интегратор',
            'vendor_product': 'Вендорский продукт',
            'version': 'Версия',
            'modules': 'Модули',
            'interfaces': 'Интерфейсы',
            'status': 'Статус',
            'installation_date': 'Дата установки',
            'notes': 'Примечания',
        }


class VendorProductForm(forms.ModelForm):
    """Форма для создания и редактирования вендорских продуктов"""

    class Meta:
        model = VendorProduct
        fields = [
            'name', 'vendor', 'product_type', 'code',
            'description', 'version', 'system_types',
            'industries', 'technical_specs', 'release_year',
            'end_of_support', 'is_active'
        ]
        widgets = {
            'release_year': forms.NumberInput(attrs={'min': 1900, 'max': 2100}),
            'end_of_support': forms.DateInput(attrs={'type': 'date'}),
            'system_types': forms.Textarea(attrs={'rows': 3}),
            'industries': forms.Textarea(attrs={'rows': 3}),
            'technical_specs': forms.Textarea(attrs={'rows': 5, 'class': 'font-monospace'}),
        }
        labels = {
            'name': 'Название продукта',
            'vendor': 'Вендор',
            'product_type': 'Тип продукта',
            'code': 'Артикул/Код',
            'description': 'Описание',
            'version': 'Версия',
            'system_types': 'Типы систем',
            'industries': 'Отрасли применения',
            'technical_specs': 'Технические характеристики',
            'release_year': 'Год выпуска',
            'end_of_support': 'Конец поддержки',
            'is_active': 'Активный продукт',
        }


class ProjectForm(forms.ModelForm):
    """Форма для создания и редактирования проектов"""

    class Meta:
        model = Project
        fields = ['name', 'participant', 'vendor_product', 'object', 'year', 'successful', 'description']
        widgets = {
            'year': forms.NumberInput(attrs={'min': 1900, 'max': 2100}),
            'description': forms.Textarea(attrs={'rows': 4}),
        }
        labels = {
            'name': 'Название проекта',
            'participant': 'Участник',
            'vendor_product': 'Вендорский продукт',
            'object': 'Объект внедрения',
            'year': 'Год реализации',
            'successful': 'Успешный пуск',
            'description': 'Описание',
        }


class CertificateForm(forms.ModelForm):
    """Форма для создания и редактирования сертификатов"""

    class Meta:
        model = Certificate
        fields = [
            'name', 'participant', 'vendor_product', 'certificate_type',
            'issued_by', 'issued_date', 'expiry_date', 'file'
        ]
        widgets = {
            'issued_date': forms.DateInput(attrs={'type': 'date'}),
            'expiry_date': forms.DateInput(attrs={'type': 'date'}),
        }
        labels = {
            'name': 'Название сертификата',
            'participant': 'Участник',
            'vendor_product': 'Вендорский продукт',
            'certificate_type': 'Тип сертификата',
            'issued_by': 'Кем выдан',
            'issued_date': 'Дата выдачи',
            'expiry_date': 'Срок действия',
            'file': 'Файл сертификата',
        }


class ReviewForm(forms.ModelForm):
    """Форма для создания и редактирования отзывов"""

    class Meta:
        model = Review
        fields = ['participant', 'text', 'rating', 'date', 'source']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'text': forms.Textarea(attrs={'rows': 4}),
        }
        labels = {
            'participant': 'Участник',
            'text': 'Текст отзыва',
            'rating': 'Оценка',
            'date': 'Дата отзыва',
            'source': 'Источник',
        }


class TCOAnalysisForm(forms.ModelForm):
    """Форма для создания и редактирования TCO анализа"""

    class Meta:
        model = TCOAnalysis
        fields = [
            'participant', 'vendor_product', 'capex',
            'opex_per_year', 'period_years', 'discount_rate', 'notes'
        ]
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
        labels = {
            'participant': 'Участник',
            'vendor_product': 'Вендорский продукт',
            'capex': 'CAPEX (млн руб)',
            'opex_per_year': 'OPEX в год (млн руб)',
            'period_years': 'Период анализа (лет)',
            'discount_rate': 'Ставка дисконтирования %',
            'notes': 'Примечания',
        }