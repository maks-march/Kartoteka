import json
import sys
from django import template
from django.utils.safestring import mark_safe
from django.core.exceptions import FieldDoesNotExist
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.html import escape

register = template.Library()


# =============================================================================
# БАЗОВЫЕ ФИЛЬТРЫ
# =============================================================================

@register.filter
def get_item(dictionary, key):
    """Получить значение из словаря по ключу"""
    if isinstance(dictionary, dict):
        return dictionary.get(key, '')
    return ''


@register.filter
def get_display(instance, field_name):
    """Получить display значение поля модели"""
    method_name = f'get_{field_name}_display'
    if hasattr(instance, method_name):
        return getattr(instance, method_name)()
    return getattr(instance, field_name, '')


@register.filter
def filter_status(objects, status):
    """Фильтровать объекты по статусу"""
    if hasattr(objects, 'filter'):
        return objects.filter(status=status)
    return [obj for obj in objects if getattr(obj, 'status') == status]


@register.filter
def filter_type(objects, obj_type):
    """Фильтровать объекты по типу"""
    if hasattr(objects, 'filter'):
        return objects.filter(object_type=obj_type)
    return [obj for obj in objects if getattr(obj, 'object_type') == obj_type]


@register.filter
def dict_get(dictionary, key):
    """Более безопасный вариант get_item с проверкой типа"""
    if not isinstance(dictionary, dict):
        return ''
    return dictionary.get(key, '')


@register.filter
def startswith(value, arg):
    """Проверяет, начинается ли строка с указанного значения"""
    if value and arg:
        return value.startswith(arg)
    return False


@register.filter
def slice_str(value, arg):
    """Срезы для строк (аналог slice:":8")"""
    try:
        if ':' in arg:
            start, end = arg.split(':')
            start = int(start) if start else 0
            end = int(end) if end else None
            return value[start:end]
    except Exception:
        return value
    return value


@register.filter
def multiply(value, arg):
    """Умножить значение"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return value


@register.filter
def divide(value, arg):
    """Разделить значение"""
    try:
        if float(arg) != 0:
            return float(value) / float(arg)
        return 0
    except (ValueError, TypeError):
        return value


@register.filter
def sum_values(values):
    """Суммировать значения (аналог sum() для шаблонов)"""
    if hasattr(values, 'values'):
        return sum(values.values())
    try:
        return sum(values)
    except TypeError:
        return len(values)


@register.filter
def filter_is_top_level(objects, is_top):
    """Фильтровать объекты по is_top_level"""
    if isinstance(is_top, str):
        is_top = is_top.lower() == 'true'
    if hasattr(objects, 'filter'):
        return objects.filter(is_top_level=is_top)
    return [
        obj for obj in objects
        if getattr(obj, 'is_top_level', False) == is_top
    ]


@register.filter
def sum_attr(items, attr_name):
    """Суммировать значения атрибута для списка объектов"""
    if not items:
        return 0

    total = 0
    for item in items:
        value = getattr(item, attr_name, 0)
        if callable(value):
            try:
                value = value()
            except Exception:
                value = 0
        try:
            if value is None:
                value = 0
            total += float(value)
        except (ValueError, TypeError):
            continue

    if isinstance(total, float) and total.is_integer():
        return int(total)
    return total


@register.filter
def filter_system_type(systems, system_type):
    """Фильтровать системы по типу (УСТАРЕЛО)"""
    if hasattr(systems, 'filter'):
        return systems.filter(system_type=system_type)
    return [sys for sys in systems if getattr(sys, 'system_type', '') == system_type]


@register.filter
def filter_system_class(systems, system_class):
    """
    Фильтровать автоматизированные системы по классу системы
    Использование: {{ systems|filter_system_class:'DCS' }}
    """
    if hasattr(systems, 'filter'):
        return systems.filter(system_class=system_class)
    return [sys for sys in systems if getattr(sys, 'system_class', '') == system_class]


@register.filter
def dictsort(items, key):
    """Сортировать по ключу (аналог dictsort)"""
    try:
        return sorted(items, key=lambda x: getattr(x, key, ''))
    except Exception:
        return items


@register.filter
def dictsortreversed(items, key):
    """Сортировать по ключу в обратном порядке"""
    try:
        return sorted(items, key=lambda x: getattr(x, key, ''), reverse=True)
    except Exception:
        return items


@register.filter
def get_item_from_list(items, index):
    """Получить элемент из списка по индексу"""
    try:
        return items[index]
    except (IndexError, TypeError):
        return None


@register.filter
def length(items):
    """Получить длину списка или QuerySet"""
    if items is None:
        return 0

    try:
        if hasattr(items, 'count'):
            return items.count()
        if hasattr(items, '__len__'):
            return len(items)
        if isinstance(items, dict):
            return len(items)
    except (AttributeError, TypeError):
        pass

    return 0


@register.filter
def participant_type(participants, type_code):
    """Фильтровать участников по типу"""
    if hasattr(participants, 'filter'):
        return participants.filter(participant_type=type_code)
    return [p for p in participants if getattr(p, 'participant_type', '') == type_code]


@register.filter
def participant_type_count(participants, type_code):
    """Возвращает количество участников указанного типа"""
    return participants.filter(participant_type=type_code).count()


@register.filter
def default_if_none(value, default):
    """Вернуть значение по умолчанию если None"""
    return value if value is not None else default


@register.filter
def truncatechars_html(value, arg):
    """Обрезать текст с сохранением HTML тегов (упрощенная версия)"""
    try:
        max_length = int(arg)
        if len(value) <= max_length:
            return value
        return value[:max_length] + '...'
    except Exception:
        return value


@register.filter
def split(value, delimiter=','):
    """
    Разделить строку по разделителю.
    Использование: {{ value|split:"," }}
    """
    if not value:
        return []

    try:
        if isinstance(value, str):
            return value.split(delimiter)
        elif isinstance(value, list):
            return value
        else:
            return str(value).split(delimiter)
    except (AttributeError, TypeError):
        return [value]


@register.filter
def get_technologies_list(participant):
    """Получить технологии участника в виде списка"""
    try:
        if hasattr(participant, 'technologies'):
            techs = list(participant.technologies.all())
            if techs:
                return [tech.name for tech in techs]

        tech_field = getattr(participant, 'technology', '')
        if tech_field:
            if isinstance(tech_field, str):
                return [t.strip() for t in tech_field.split(',') if t.strip()]
            return [str(tech_field)]
    except Exception as e:
        print(f"Error in get_technologies_list: {e}")

    return []


# =============================================================================
# ФИЛЬТРЫ ДЛЯ УЛУЧШЕНИЯ ШАБЛОНОВ
# =============================================================================

@register.filter
def get_attr(obj, attr_name):
    """Безопасно получить атрибут объекта по имени"""
    try:
        return getattr(obj, attr_name, '')
    except (AttributeError, TypeError):
        return ''


@register.filter
def get_nested_attr(obj, attr_path):
    """Получить вложенный атрибут через точку (obj.attr1.attr2)"""
    try:
        value = obj
        for attr in attr_path.split('.'):
            value = getattr(value, attr, None)
            if value is None:
                return ''
        return value
    except (AttributeError, TypeError):
        return ''


@register.filter
def get_verbose_name(obj, field_name):
    """Получить verbose_name поля модели"""
    try:
        return obj._meta.get_field(field_name).verbose_name
    except (AttributeError, FieldDoesNotExist):
        return field_name


@register.filter
def get_help_text(obj, field_name):
    """Получить help_text поля модели"""
    try:
        return obj._meta.get_field(field_name).help_text
    except (AttributeError, FieldDoesNotExist):
        return ''


@register.filter
def format_json(value, indent=2):
    """Форматировать JSON для отображения"""
    if not value:
        return ''
    try:
        if isinstance(value, str):
            data = json.loads(value)
        else:
            data = value
        return mark_safe(
            f'<pre class="json-view">'
            f'{json.dumps(data, indent=indent, ensure_ascii=False)}'
            f'</pre>'
        )
    except Exception:
        return value


@register.filter
def get_year(date_value):
    """Извлечь год из даты"""
    if hasattr(date_value, 'year'):
        return date_value.year
    return ''


@register.filter
def month_name(date_value):
    """Получить название месяца"""
    if hasattr(date_value, 'strftime'):
        months = [
            'января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
            'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря',
        ]
        try:
            return months[date_value.month - 1]
        except Exception:
            return date_value.strftime('%B')
    return ''


@register.filter
def filesizeformat(bytes_value):
    """Форматировать размер файла"""
    try:
        bytes_value = float(bytes_value)
    except (TypeError, ValueError):
        return '0 Б'

    if bytes_value < 1024:
        return f'{bytes_value:.0f} Б'
    elif bytes_value < 1024 ** 2:
        return f'{bytes_value / 1024:.1f} КБ'
    elif bytes_value < 1024 ** 3:
        return f'{bytes_value / 1024 ** 2:.1f} МБ'
    else:
        return f'{bytes_value / 1024 ** 3:.1f} ГБ'


@register.filter
def percentage(value, total):
    """Вычислить процент"""
    try:
        if float(total) == 0:
            return 0
        return round((float(value) / float(total)) * 100, 1)
    except (ValueError, TypeError):
        return 0


@register.filter
def yesno(value, arg=None):
    """Аналог yesno, но для булевых значений"""
    if arg:
        true_str, false_str = arg.split(',')[:2]
    else:
        true_str, false_str = 'Да', 'Нет'

    if value:
        return true_str
    return false_str


@register.filter
def get_range(value):
    """Создать диапазон чисел для циклов"""
    try:
        return range(int(value))
    except (ValueError, TypeError):
        return range(0)


@register.filter
def get_index(sequence, index):
    """Получить элемент по индексу"""
    try:
        return sequence[int(index)]
    except (IndexError, TypeError, ValueError):
        return None


@register.filter
def is_empty(value):
    """Проверить, пустое ли значение"""
    if value is None:
        return True
    if hasattr(value, '__len__'):
        return len(value) == 0
    return False


@register.filter
def is_not_empty(value):
    """Проверить, не пустое ли значение"""
    return not is_empty(value)


@register.filter
def truncate_middle(value, arg):
    """Обрезать середину строки"""
    try:
        max_length = int(arg)
        if len(value) <= max_length:
            return value
        half = max_length // 2
        return value[:half] + '…' + value[-half:]
    except Exception:
        return value


@register.filter
def phone_format(phone):
    """Форматировать телефонный номер"""
    if not phone:
        return ''

    digits = ''.join(filter(str.isdigit, str(phone)))

    if len(digits) == 11:
        return (
            f'+{digits[0]} ({digits[1:4]}) '
            f'{digits[4:7]}-{digits[7:9]}-{digits[9:11]}'
        )
    elif len(digits) == 10:
        return (
            f'+7 ({digits[0:3]}) '
            f'{digits[3:6]}-{digits[6:8]}-{digits[8:10]}'
        )
    else:
        return phone


@register.filter
def inn_format(inn):
    """Форматировать ИНН"""
    if not inn:
        return ''

    inn_str = str(inn)
    if len(inn_str) == 10:
        return (
            f'{inn_str[0:2]} {inn_str[2:5]} '
            f'{inn_str[5:8]} {inn_str[8:10]}'
        )
    elif len(inn_str) == 12:
        return (
            f'{inn_str[0:3]} {inn_str[3:6]} '
            f'{inn_str[6:9]} {inn_str[9:12]}'
        )
    else:
        return inn_str


@register.filter
def kpp_format(kpp):
    """Форматировать КПП"""
    if not kpp:
        return ''
    kpp_str = str(kpp)
    if len(kpp_str) == 9:
        return f'{kpp_str[0:4]} {kpp_str[4:7]} {kpp_str[7:9]}'
    return kpp_str


@register.filter
def ogrn_format(ogrn):
    """Форматировать ОГРН"""
    if not ogrn:
        return ''
    ogrn_str = str(ogrn)
    if len(ogrn_str) == 13:
        return f'{ogrn_str[0:2]} {ogrn_str[2:5]} {ogrn_str[5:9]} {ogrn_str[9:13]}'
    return ogrn_str


@register.filter
def highlight(text, search_term, case_sensitive=False):
    """Подсветить поисковый запрос в тексте"""
    if not text or not search_term:
        return text

    text = str(text)
    search = str(search_term)

    if not case_sensitive:
        text_lower = text.lower()
        search_lower = search.lower()

        positions = []
        start = 0
        while True:
            pos = text_lower.find(search_lower, start)
            if pos == -1:
                break
            positions.append((pos, pos + len(search)))
            start = pos + 1

        if positions:
            result = []
            last_end = 0
            for start, end in positions:
                result.append(text[last_end:start])
                result.append(f'<mark>{text[start:end]}</mark>')
                last_end = end
            result.append(text[last_end:])
            return mark_safe(''.join(result))

    return text


@register.filter
def format_capacity(value):
    """Форматировать мощность (тыс. тонн/год)"""
    try:
        val = float(value)
        if val >= 1000:
            return f'{val / 1000:.1f} млн т/год'
        else:
            return f'{val:.0f} тыс т/год'
    except (ValueError, TypeError):
        return value


@register.filter
def get_system_color(system_class):
    """Получить цвет для класса системы"""
    colors = {
        'DCS': '#FF6384',
        'SCADA': '#36A2EB',
        'MES': '#FFCE56',
        'PLC': '#4BC0C0',
        'ESD': '#9966FF',
        'SENSORS': '#FF9F40',
    }
    return colors.get(system_class, '#95A5A6')


@register.filter
def get_status_color(status):
    """Получить цвет для статуса"""
    colors = {
        'ACTIVE': '#28a745',
        'PROJECT': '#17a2b8',
        'RECONSTRUCTION': '#ffc107',
        'STOPPED': '#dc3545',
        'COMPLETED': '#28a745',
        'PLANNED': '#17a2b8',
        'IN_PROGRESS': '#ffc107',
    }
    return colors.get(status, '#6c757d')


@register.filter
def group_by(queryset, key):
    """Сгруппировать объекты по ключу"""
    result = {}
    for obj in queryset:
        value = getattr(obj, key, None)
        if value not in result:
            result[value] = []
        result[value].append(obj)
    return result


@register.filter
def to_class_name(value):
    """Получить имя класса объекта"""
    if hasattr(value, '__class__'):
        return value.__class__.__name__
    return ''


@register.filter
def model_verbose_name(model):
    """Получить verbose_name модели"""
    if hasattr(model, '_meta'):
        return model._meta.verbose_name
    return ''


@register.filter
def model_verbose_name_plural(model):
    """Получить verbose_name_plural модели"""
    if hasattr(model, '_meta'):
        return model._meta.verbose_name_plural
    return ''


# =============================================================================
# ФИЛЬТРЫ ДЛЯ КЛАССОВ СИСТЕМ
# =============================================================================

@register.filter
def get_system_class_short(value):
    """Возвращает краткое обозначение класса системы"""
    if not value:
        return value

    value = str(value).strip()

    class_mapping = {
        'DCS': 'DCS',
        'Distributed Control System': 'DCS',
        'Распределённая система управления': 'DCS',
        'Распределенная система управления': 'DCS',
        'Распределённая система управления (Distributed Control System)': 'DCS',
        'Распределенная система управления (Distributed Control System)': 'DCS',

        'SCADA': 'SCADA',
        'Supervisory Control and Data Acquisition': 'SCADA',
        'Supervisory Control And Data Acquisition': 'SCADA',
        'Диспетчерское управление': 'SCADA',
        'Диспетчерское управление и сбор данных': 'SCADA',
        'Диспетчерское управление и сбор данных (SCADA)': 'SCADA',

        'PLC': 'ПЛК',
        'Programmable Logic Controller': 'ПЛК',
        'Программируемый логический контроллер': 'ПЛК',
        'Программируемый логический контроллер (PLC)': 'ПЛК',

        'MES': 'MES',
        'Manufacturing Execution System': 'MES',
        'Производственная исполнительная система': 'MES',
        'MES-система': 'MES',
        'Производственная исполнительная система (MES)': 'MES',

        'APCS': 'АСУТП',
        'Automated Process Control System': 'АСУТП',
        'АСУТП': 'АСУТП',
        'Автоматизированная система управления технологическим процессом': 'АСУТП',
        'Автоматизированная система управления технологическим процессом (АСУТП)': 'АСУТП',

        'HMI': 'HMI',
        'Human-Machine Interface': 'HMI',
        'Человеко-машинный интерфейс': 'HMI',
        'Человеко-машинный интерфейс (HMI)': 'HMI',

        'ERP': 'ERP',
        'Enterprise Resource Planning': 'ERP',
        'Планирование ресурсов предприятия': 'ERP',
        'Планирование ресурсов предприятия (ERP)': 'ERP',

        'EAM': 'EAM',
        'Enterprise Asset Management': 'EAM',
        'Управление основными фондами': 'EAM',
        'Управление основными фондами (EAM)': 'EAM',

        'CMMS': 'CMMS',
        'Computerized Maintenance Management System': 'CMMS',
        'Управление техобслуживанием и ремонтами': 'CMMS',
        'Управление техобслуживанием и ремонтами (CMMS)': 'CMMS',

        'LIMS': 'LIMS',
        'Laboratory Information Management System': 'LIMS',
        'Лабораторная информационная система': 'LIMS',
        'Лабораторная информационная система (LIMS)': 'LIMS',

        'WMS': 'WMS',
        'Warehouse Management System': 'WMS',
        'Управление складом': 'WMS',
        'Управление складом (WMS)': 'WMS',

        'EMS': 'EMS',
        'Energy Management System': 'EMS',
        'Управление энергоресурсами': 'EMS',
        'Управление энергоресурсами (EMS)': 'EMS',

        'APC': 'APC',
        'Advanced Process Control': 'APC',
        'Передовое управление процессами': 'APC',
        'Передовое управление процессами (APC)': 'APC',

        'RTO': 'RTO',
        'Real-Time Optimization': 'RTO',
        'Оптимизация в реальном времени': 'RTO',
        'Оптимизация в реальном времени (RTO)': 'RTO',

        'PAC': 'PAC',
        'Programmable Automation Controller': 'PAC',
        'Программируемый автомат': 'PAC',
        'Программируемый автомат (PAC)': 'PAC',

        'RTU': 'RTU',
        'Remote Terminal Unit': 'RTU',
        'Удалённый терминал': 'RTU',
        'Удалённый терминал (RTU)': 'RTU',

        'SIS': 'СИЗБ',
        'Safety Instrumented System': 'СИЗБ',
        'Система безопасности': 'СИЗБ',
        'Система безопасности (СИЗБ)': 'СИЗБ',

        'ESD': 'ПАЗ',
        'Emergency Shutdown': 'ПАЗ',
        'Противоаварийная защита': 'ПАЗ',
        'Противоаварийная защита (ПАЗ)': 'ПАЗ',

        'F&G': 'F&G',
        'Fire & Gas': 'F&G',
        'Обнаружение пожара и газа': 'F&G',
        'Обнаружение пожара и газа (F&G)': 'F&G',

        'PCS': 'PCS',
        'Process Control System': 'PCS',
        'Управление процессами': 'PCS',
        'Управление процессами (PCS)': 'PCS',
    }

    if value in class_mapping:
        return class_mapping[value]

    value_lower = value.lower()
    for key, short in class_mapping.items():
        if key.lower() in value_lower:
            return short

    if len(value) > 20:
        return value[:15] + '…'
    return value


@register.filter
def get_system_class_full_name(value):
    """Возвращает полное название класса системы"""
    if not value:
        return value

    value = str(value).strip()

    full_names = {
        'DCS': 'Распределённая система управления (Distributed Control System)',
        'SCADA': 'Диспетчерское управление и сбор данных (Supervisory Control and Data Acquisition)',
        'ПЛК': 'Программируемый логический контроллер (Programmable Logic Controller)',
        'PLC': 'Программируемый логический контроллер (Programmable Logic Controller)',
        'MES': 'Производственная исполнительная система (Manufacturing Execution System)',
        'АСУТП': 'Автоматизированная система управления технологическим процессом',
        'APCS': 'Автоматизированная система управления технологическим процессом',
        'HMI': 'Человеко-машинный интерфейс (Human-Machine Interface)',
        'ERP': 'Планирование ресурсов предприятия (Enterprise Resource Planning)',
        'EAM': 'Управление основными фондами (Enterprise Asset Management)',
        'CMMS': 'Управление техобслуживанием и ремонтами (Computerized Maintenance Management System)',
        'LIMS': 'Лабораторная информационная система (Laboratory Information Management System)',
        'WMS': 'Управление складом (Warehouse Management System)',
        'EMS': 'Управление энергоресурсами (Energy Management System)',
        'APC': 'Передовое управление процессами (Advanced Process Control)',
        'RTO': 'Оптимизация в реальном времени (Real-Time Optimization)',
        'PAC': 'Программируемый автомат (Programmable Automation Controller)',
        'RTU': 'Удалённый терминал (Remote Terminal Unit)',
        'СИЗБ': 'Система безопасности (Safety Instrumented System)',
        'ПАЗ': 'Противоаварийная защита (Emergency Shutdown)',
        'F&G': 'Обнаружение пожара и газа (Fire & Gas)',
        'PCS': 'Управление процессами (Process Control System)',
    }

    if value in full_names:
        return full_names[value]

    class_mapping = {
        'Распределённая система управления': 'DCS',
        'Распределенная система управления': 'DCS',
        'Диспетчерское управление': 'SCADA',
        'Программируемый логический контроллер': 'ПЛК',
        'Производственная исполнительная система': 'MES',
        'MES-система': 'MES',
        'Автоматизированная система управления технологическим процессом': 'АСУТП',
        'Человеко-машинный интерфейс': 'HMI',
        'Планирование ресурсов предприятия': 'ERP',
        'Управление основными фондами': 'EAM',
        'Управление техобслуживанием и ремонтами': 'CMMS',
        'Лабораторная информационная система': 'LIMS',
        'Управление складом': 'WMS',
        'Управление энергоресурсами': 'EMS',
        'Передовое управление процессами': 'APC',
        'Оптимизация в реальном времени': 'RTO',
        'Программируемый автомат': 'PAC',
        'Удалённый терминал': 'RTU',
        'Система безопасности': 'СИЗБ',
        'Противоаварийная защита': 'ПАЗ',
        'Обнаружение пожара и газа': 'F&G',
        'Управление процессами': 'PCS',
    }

    if value in class_mapping:
        short = class_mapping[value]
        return full_names.get(short, value)

    return value


@register.filter
def get_all_system_classes(clients_list):
    """Собирает уникальные классы систем из всех клиентов"""
    all_classes = set()
    for client in clients_list:
        if isinstance(client, dict) and client.get('system_classes'):
            if isinstance(client['system_classes'], list):
                for class_name in client['system_classes']:
                    if class_name:
                        all_classes.add(str(class_name).strip())
    return sorted(list(all_classes))


@register.filter
def jsonify(value):
    """
    Преобразует значение в JSON строку для безопасного использования в JavaScript.
    Использование: {{ graph_data|jsonify|safe }}
    """
    try:
        return json.dumps(value, ensure_ascii=False, cls=DjangoJSONEncoder)
    except (TypeError, ValueError):
        return '{}'


# =============================================================================
# ФИЛЬТРЫ ДЛЯ ГРАФА СВЯЗЕЙ
# =============================================================================

@register.filter
def graph_node_color(node_type, hierarchy_level=None):
    """
    Возвращает цвет для узла графа
    Использование: {{ node.type|graph_node_color:node.hierarchy_level }}
    """
    colors = {
        'object': {
            'LEVEL_1': '#E74C3C',
            'LEVEL_2': '#F39C12',
            'LEVEL_3': '#3498DB',
            'default': '#3498DB',
        },
        'vendor': '#2ECC71',
        'integrator': '#9B59B6',
        'system': '#F1C40F',
        'supplier': '#7F8C8D',
        'default': '#95A5A6',
    }

    if node_type in colors:
        if isinstance(colors[node_type], dict):
            return colors[node_type].get(hierarchy_level, colors[node_type]['default'])
        return colors[node_type]
    return colors['default']


@register.filter
def graph_node_shape(node_type):
    """
    Возвращает форму узла в зависимости от типа
    Использование: {{ node.type|graph_node_shape }}
    """
    shapes = {
        'object': 'box',
        'vendor': 'dot',
        'integrator': 'dot',
        'system': 'database',
        'supplier': 'dot',
        'default': 'dot',
    }
    return shapes.get(node_type, shapes['default'])


@register.filter
def graph_node_size(node_type, system_count=0):
    """
    Возвращает размер узла (с учетом количества систем для вендоров)
    Использование: {{ node.type|graph_node_size:node.system_count }}
    """
    base_sizes = {
        'object': {
            'LEVEL_1': 30,
            'LEVEL_2': 25,
            'LEVEL_3': 20,
            'default': 20,
        },
        'vendor': 20,
        'integrator': 18,
        'system': 14,
        'supplier': 16,
        'default': 15,
    }

    if node_type == 'vendor' and system_count:
        return min(20 + int(system_count) * 2, 40)

    if node_type in base_sizes:
        if isinstance(base_sizes[node_type], dict):
            return base_sizes[node_type].get('LEVEL_1', base_sizes[node_type]['default'])
        return base_sizes[node_type]
    return base_sizes['default']


@register.filter
def graph_edge_color(edge_type):
    """
    Возвращает цвет для ребра графа
    Использование: {{ edge.type|graph_edge_color }}
    """
    colors = {
        'hierarchy': '#95A5A6',
        'vendor_to_system': '#2ECC71',
        'system_to_object': '#F1C40F',
        'integrator_to_system': '#9B59B6',
        'default': '#95A5A6',
    }
    return colors.get(edge_type, colors['default'])


@register.filter
def graph_edge_label(edge_type):
    """
    Возвращает подпись для ребра графа
    Использование: {{ edge.type|graph_edge_label }}
    """
    labels = {
        'hierarchy': 'включает',
        'vendor_to_system': 'поставляет',
        'system_to_object': 'установлена',
        'integrator_to_system': 'внедряет',
        'default': 'связан',
    }
    return labels.get(edge_type, labels['default'])


@register.filter
def graph_edge_style(edge_type):
    """
    Возвращает стиль ребра (сплошная/пунктир)
    Использование: {{ edge.type|graph_edge_style }}
    """
    styles = {
        'hierarchy': False,
        'vendor_to_system': False,
        'system_to_object': False,
        'integrator_to_system': True,
        'default': False,
    }
    return styles.get(edge_type, styles['default'])


@register.filter
def filter_nodes_by_type(nodes, node_type):
    """
    Фильтрует узлы по типу
    Использование: {{ nodes|filter_nodes_by_type:'vendor' }}
    """
    if not nodes:
        return []

    filtered = []
    for node in nodes:
        node_id = node.get('id', '')
        if node_type == 'object' and node_id.startswith('obj_'):
            filtered.append(node)
        elif node_type == 'vendor' and node_id.startswith('part_') and node.get('group') == 'vendor':
            filtered.append(node)
        elif node_type == 'integrator' and node_id.startswith('part_') and node.get('group') == 'integrator':
            filtered.append(node)
        elif node_type == 'system' and node_id.startswith('sys_'):
            filtered.append(node)
        elif node_type == 'supplier' and node_id.startswith('part_') and node.get('group') == 'supplier':
            filtered.append(node)
    return filtered


@register.filter
def filter_edges_by_type(edges, edge_type):
    """
    Фильтрует ребра по типу
    Использование: {{ edges|filter_edges_by_type:'hierarchy' }}
    """
    if not edges:
        return []

    filtered = []
    for edge in edges:
        label = edge.get('label', '')
        if edge_type == 'hierarchy' and label == 'включает':
            filtered.append(edge)
        elif edge_type == 'vendor_to_system' and label == 'поставляет':
            filtered.append(edge)
        elif edge_type == 'system_to_object' and label == 'установлена':
            filtered.append(edge)
        elif edge_type == 'integrator_to_system' and label == 'внедряет':
            filtered.append(edge)
    return filtered


@register.filter
def count_by_type(items, type_name):
    """
    Подсчитывает количество элементов определенного типа
    Использование: {{ nodes|count_by_type:'vendor' }}
    """
    if not items:
        return 0

    count = 0
    for item in items:
        item_id = item.get('id', '')
        item_group = item.get('group', '')

        if type_name == 'object' and item_id.startswith('obj_'):
            count += 1
        elif type_name == 'vendor' and item_id.startswith('part_') and item_group == 'vendor':
            count += 1
        elif type_name == 'integrator' and item_id.startswith('part_') and item_group == 'integrator':
            count += 1
        elif type_name == 'system' and item_id.startswith('sys_'):
            count += 1
        elif type_name == 'supplier' and item_id.startswith('part_') and item_group == 'supplier':
            count += 1
    return count


@register.filter
def get_node_connections(node_id, edges):
    """
    Возвращает все связи для указанного узла
    Использование: {{ node.id|get_node_connections:edges }}
    """
    if not edges:
        return []

    connections = []
    for edge in edges:
        if edge.get('from') == node_id or edge.get('to') == node_id:
            connections.append(edge)
    return connections


@register.filter
def get_connected_nodes(node_id, edges, nodes):
    """
    Возвращает все узлы, связанные с указанным
    Использование: {{ node.id|get_connected_nodes:edges:graphData.nodes }}
    """
    if not edges or not nodes:
        return []

    connected_ids = set()
    for edge in edges:
        if edge.get('from') == node_id:
            connected_ids.add(edge.get('to'))
        if edge.get('to') == node_id:
            connected_ids.add(edge.get('from'))

    connected_nodes = []
    nodes_dict = {node.get('id'): node for node in nodes if node.get('id')}

    for connected_id in connected_ids:
        if connected_id in nodes_dict:
            connected_nodes.append(nodes_dict[connected_id])

    return connected_nodes


@register.filter
def get_node_by_id(nodes, node_id):
    """
    Находит узел по ID
    Использование: {{ nodes|get_node_by_id:'obj_1' }}
    """
    if not nodes:
        return None

    for node in nodes:
        if node.get('id') == node_id:
            return node
    return None


@register.filter
def get_node_label(node_id, nodes):
    """
    Возвращает подпись узла по его ID
    Использование: {{ edge.from|get_node_label:nodes }}
    """
    node = get_node_by_id(nodes, node_id)
    if node:
        return node.get('label', node_id)
    return node_id


@register.filter
def get_node_type(node_id):
    """
    Определяет тип узла по его ID
    Использование: {{ node.id|get_node_type }}
    """
    if node_id.startswith('obj_'):
        return 'object'
    elif node_id.startswith('sys_'):
        return 'system'
    elif node_id.startswith('part_'):
        return 'participant'
    return 'unknown'


@register.filter
def get_node_group(node_id):
    """
    Определяет группу узла по его ID (для стилизации)
    Использование: {{ node.id|get_node_group }}
    """
    if node_id.startswith('obj_'):
        return 'object'
    elif node_id.startswith('sys_'):
        return 'system'
    elif node_id.startswith('part_'):
        return 'participant'
    return 'default'


@register.filter
def format_node_title(node):
    """
    Форматирует заголовок узла для всплывающей подсказки
    Использование: {{ node|format_node_title }}
    """
    if not node:
        return ''

    node_id = node.get('id', '')
    node_label = node.get('label', '')
    node_title = node.get('title', '')

    if node_title:
        return node_title

    if node_id.startswith('obj_'):
        return f"Объект: {node_label}"
    elif node_id.startswith('sys_'):
        return f"Система: {node_label}"
    elif node_id.startswith('part_'):
        return f"Участник: {node_label}"

    return node_label


@register.filter
def graph_stats(nodes, edges):
    """
    Возвращает статистику по графу
    Использование: {{ nodes|graph_stats:edges }}
    """
    stats = {
        'total_nodes': len(nodes) if nodes else 0,
        'total_edges': len(edges) if edges else 0,
        'object': count_by_type(nodes, 'object') if nodes else 0,
        'vendors': count_by_type(nodes, 'vendor') if nodes else 0,
        'integrators': count_by_type(nodes, 'integrator') if nodes else 0,
        'systems': count_by_type(nodes, 'system') if nodes else 0,
        'suppliers': count_by_type(nodes, 'supplier') if nodes else 0,
    }

    if edges:
        stats['hierarchy_edges'] = len(filter_edges_by_type(edges, 'hierarchy'))
        stats['vendor_edges'] = len(filter_edges_by_type(edges, 'vendor_to_system'))
        stats['system_edges'] = len(filter_edges_by_type(edges, 'system_to_object'))
        stats['integrator_edges'] = len(filter_edges_by_type(edges, 'integrator_to_system'))
    else:
        stats.update({
            'hierarchy_edges': 0,
            'vendor_edges': 0,
            'system_edges': 0,
            'integrator_edges': 0,
        })

    return stats


@register.filter
def json_script(value, element_id):
    """
    Безопасно встраивает JSON данные в script тег
    Использование: {{ graph_data|json_script:'graph-data' }}
    """
    json_str = json.dumps(value, ensure_ascii=False, cls=DjangoJSONEncoder)
    return mark_safe(
        f'<script id="{element_id}" type="application/json">{escape(json_str)}</script>'
    )


@register.filter
def debug_dump(value):
    """Отладочный фильтр для просмотра структуры данных"""
    print(f"DEBUG DUMP - Type: {type(value)}", file=sys.stderr)
    if hasattr(value, '__len__'):
        print(f"DEBUG DUMP - Length: {len(value)}", file=sys.stderr)
    if isinstance(value, dict):
        print(f"DEBUG DUMP - Keys: {list(value.keys())}", file=sys.stderr)
    elif isinstance(value, list) and len(value) > 0:
        first_item_keys = (
            list(value[0].keys())
            if isinstance(value[0], dict)
            else 'not dict'
        )
        print(f"DEBUG DUMP - First item keys: {first_item_keys}", file=sys.stderr)
    return value


@register.filter
def format_money(value):
    """Форматирование денежных значений"""
    try:
        val = float(value)
        if val >= 1000:
            return f"{val / 1000:.1f} млрд"
        return f"{val:.1f} млн"
    except (ValueError, TypeError):
        return "0"
