import csv
import io
import json
import logging
import time

import chardet
from django.urls import reverse
from django.core.cache import cache
from django.core.paginator import Paginator
from django.db import connection
from django.db.models import Count, Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User, Group
from networkx import nodes, edges
from django.core.serializers.json import DjangoJSONEncoder

from .audit import AuditManager
from .decorators import (
    group_required, editor_required, viewer_required,
    can_edit_object, can_delete_object
)
from .forms import (
    ObjectForm, ParticipantForm, AutomatedSystemForm,
    VendorProductForm, ProjectForm
)
from .models import (
    SYSTEM_CLASSES,
    Address,
    AutomatedSystem,
    AutomationLevel,
    CompanyGroup,
    LegalEntity,
    Object,
    ObjectAutomationLevel,
    ObjectClass,
    Participant,
    Project,
    VendorProduct,
)

logger = logging.getLogger(__name__)


# =============================================================================
# ЭКСПОРТ ДАННЫХ
# =============================================================================

@login_required
@viewer_required
def export_data(request):
    """Экспорт данных в CSV/JSON"""
    export_format = request.GET.get('format', 'csv')
    model_type = request.GET.get('model', 'objects')

    if export_format == 'json':
        response = HttpResponse(content_type='application/json')
        response['Content-Disposition'] = (
            f'attachment; filename="{model_type}_export.json"'
        )

        if model_type == 'objects':
            objects_data = []
            for obj in Object.objects.all():
                objects_data.append({
                    'id': obj.id,
                    'name': obj.name,
                    'short_name': obj.short_name,
                    'hierarchy_level': obj.hierarchy_level,
                    'technology': obj.technology,
                    'start_year': obj.start_year,
                    'capacity': float(obj.capacity) if obj.capacity else None,
                    'status': obj.status,
                    'object_class_id': obj.object_class_id,
                    'legal_entity_id': obj.legal_entity_id,
                    'address_id': obj.address_id,
                })
            data = objects_data

        elif model_type == 'participants':
            data = list(Participant.objects.values(
                'id', 'name', 'inn', 'participant_type', 'is_partner',
                'website', 'kam_name', 'kam_phone', 'profile'
            ))
        elif model_type == 'systems':
            data = list(AutomatedSystem.objects.values(
                'id', 'name', 'system_class', 'object_id',
                'vendor_id', 'integrator_id', 'status', 'version'
            ))
        elif model_type == 'all':
            objects_data = []
            for obj in Object.objects.all():
                objects_data.append({
                    'id': obj.id,
                    'name': obj.name,
                    'short_name': obj.short_name,
                    'hierarchy_level': obj.hierarchy_level,
                    'technology': obj.technology,
                    'start_year': obj.start_year,
                    'capacity': float(obj.capacity) if obj.capacity else None,
                    'status': obj.status,
                })

            data = {
                'objects': objects_data,
                'participants': list(Participant.objects.values(
                    'id', 'name', 'inn', 'participant_type', 'is_partner',
                )),
                'systems': list(AutomatedSystem.objects.values(
                    'id', 'name', 'system_class', 'object_id', 'vendor_id', 'status',
                )),
            }
        else:
            data = {'error': 'Unknown model type'}

        json_str = json.dumps(data, ensure_ascii=False, indent=2, cls=DjangoJSONEncoder)
        response.write(json_str)
        return response

    else:
        # CSV экспорт (без изменений)
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = (
            f'attachment; filename="{model_type}_export.csv"'
        )
        writer = csv.writer(response)

        if model_type == 'objects':
            _export_objects(writer)
        elif model_type == 'participants':
            _export_participants(writer)
        elif model_type == 'systems':
            _export_systems(writer)
        elif model_type == 'all':
            writer.writerow(['=== ОБЪЕКТЫ ==='])
            _export_objects(writer)
            writer.writerow([])
            writer.writerow(['=== УЧАСТНИКИ ==='])
            _export_participants(writer)
            writer.writerow([])
            writer.writerow(['=== СИСТЕМЫ ==='])
            _export_systems(writer)

        return response


def _export_objects(writer):
    """Экспорт объектов в CSV"""
    writer.writerow([
        'ID', 'Название', 'Короткое имя', 'Уровень', 'Класс', 'Технология',
        'Категория', 'Год ввода', 'Мощность', 'Статус', 'Юрлицо',
    ])
    for obj in Object.objects.all().select_related(
        'object_class', 'legal_entity'
    ):
        writer.writerow([
            obj.id,
            obj.name,
            obj.short_name or '',
            obj.get_hierarchy_level_display(),
            obj.object_class.name if obj.object_class else '',
            obj.technology,
            obj.get_category_display(),
            obj.start_year,
            str(obj.capacity),
            obj.get_status_display(),
            obj.legal_entity.name if obj.legal_entity else '',
        ])


def _export_participants(writer):
    """Экспорт участников в CSV"""
    writer.writerow([
        'ID', 'Название', 'ИНН', 'Тип', 'Партнер', 'Сайт', 'КАМ', 'Телефон КАМ',
    ])
    for p in Participant.objects.all():
        writer.writerow([
            p.id,
            p.name,
            p.inn,
            p.get_participant_type_display(),
            'Да' if p.is_partner else 'Нет',
            p.website or '',
            p.kam_name or '',
            p.kam_phone or '',
        ])


def _export_systems(writer):
    """Экспорт систем в CSV"""
    writer.writerow([
        'ID', 'Название', 'Класс', 'Объект', 'Вендор', 'Интегратор', 'Статус',
    ])
    for s in AutomatedSystem.objects.all().select_related(
        'object', 'vendor', 'integrator'
    ):
        writer.writerow([
            s.id,
            s.name,
            s.get_system_class_display() if s.system_class else '',
            s.object.name if s.object else '',
            s.vendor.name if s.vendor else '',
            s.integrator.name if s.integrator else '',
            s.get_status_display(),
        ])


def _export_all_json():
    """Экспорт всех данных в JSON"""
    data = {
        'objects': list(Object.objects.values(
            'id', 'name', 'short_name', 'hierarchy_level',
            'technology', 'start_year', 'capacity', 'status',
        )),
        'participants': list(Participant.objects.values(
            'id', 'name', 'inn', 'participant_type', 'is_partner',
        )),
        'systems': list(AutomatedSystem.objects.values(
            'id', 'name', 'system_class', 'object_id', 'vendor_id', 'status',
        )),
    }
    return JsonResponse(
        data,
        json_dumps_params={'ensure_ascii': False, 'indent': 2},
    )


# =============================================================================
# ИМПОРТ ДАННЫХ
# =============================================================================

@login_required
@editor_required
def import_data(request):
    """Импорт данных из CSV или JSON файлов"""
    if request.method != 'POST' or not request.FILES.getlist('files'):
        return redirect('export_import_page')

    files = request.FILES.getlist('files')
    total_success = 0
    total_errors = 0
    all_messages = []

    json_files = [f for f in files if f.name.endswith('.json')]
    csv_files = [f for f in files if f.name.endswith('.csv')]

    # Обработка JSON файлов
    for json_file in json_files:
        success, errors, messages = _process_json_file(json_file)
        total_success += success
        total_errors += errors
        all_messages.extend(messages)

    # Обработка CSV файлов
    for csv_file in csv_files:
        success, errors, messages = _process_csv_file(csv_file)
        total_success += success
        total_errors += errors
        all_messages.extend(messages)

    # Формируем сообщение
    if all_messages:
        messages.warning(
            request,
            f'Успешно: {total_success}, Ошибок: {total_errors}\n'
            + '\n'.join(all_messages[:15])
        )
    else:
        messages.success(
            request,
            f'Импорт успешно завершен! Добавлено: {total_success}'
        )

    return redirect('export_import_page')


def _process_json_file(json_file):
    """Обработка одного JSON файла"""
    success = 0
    errors = 0
    messages = []

    try:
        content = json_file.read().decode('utf-8')
        data = json.loads(content)

        if isinstance(data, dict):
            # Импортируем участников
            if 'participants' in data:
                for item in data['participants']:
                    try:
                        import_participant_item(item)
                        success += 1
                    except Exception as e:
                        errors += 1
                        messages.append(
                            f"JSON {json_file.name} - участник: {str(e)}"
                        )

            # Импортируем объекты
            if 'objects' in data:
                for item in data['objects']:
                    try:
                        import_object_item(item)
                        success += 1
                    except Exception as e:
                        errors += 1
                        messages.append(
                            f"JSON {json_file.name} - объект: {str(e)}"
                        )

            # Импортируем системы
            if 'systems' in data:
                for item in data['systems']:
                    try:
                        import_system_item(item)
                        success += 1
                    except Exception as e:
                        errors += 1
                        messages.append(
                            f"JSON {json_file.name} - система: {str(e)}"
                        )

            # Импортируем уровни
            if 'levels' in data:
                for item in data['levels']:
                    try:
                        import_level_item(item)
                        success += 1
                    except Exception as e:
                        errors += 1
                        messages.append(
                            f"JSON {json_file.name} - уровень: {str(e)}"
                        )

        elif isinstance(data, list) and data:
            first_item = data[0]
            if 'inn' in first_item:
                for item in data:
                    try:
                        import_participant_item(item)
                        success += 1
                    except Exception as e:
                        errors += 1
                        messages.append(
                            f"JSON {json_file.name} - участник: {str(e)}"
                        )
            elif 'hierarchy_level' in first_item:
                for item in data:
                    try:
                        import_object_item(item)
                        success += 1
                    except Exception as e:
                        errors += 1
                        messages.append(
                            f"JSON {json_file.name} - объект: {str(e)}"
                        )
            elif 'system_class' in first_item:
                for item in data:
                    try:
                        import_system_item(item)
                        success += 1
                    except Exception as e:
                        errors += 1
                        messages.append(
                            f"JSON {json_file.name} - система: {str(e)}"
                        )

    except Exception as e:
        errors += 1
        messages.append(f"Ошибка в JSON {json_file.name}: {str(e)}")

    return success, errors, messages


def _process_csv_file(csv_file):
    """Обработка одного CSV файла"""
    success = 0
    errors = 0
    messages = []

    try:
        file_name = csv_file.name.lower()
        raw_data = csv_file.read()
        encoding = chardet.detect(raw_data)['encoding'] or 'utf-8'
        decoded = raw_data.decode(encoding)
        reader = csv.DictReader(io.StringIO(decoded))
        rows = list(reader)

        if not rows:
            return success, errors, messages

        if 'participant' in file_name or 'участник' in file_name:
            for row in rows:
                try:
                    import_participant_from_dict(row)
                    success += 1
                except Exception as e:
                    errors += 1
                    messages.append(f"{csv_file.name}: {str(e)}")

        elif 'object' in file_name or 'объект' in file_name:
            for row in rows:
                try:
                    import_object_from_dict(row)
                    success += 1
                except Exception as e:
                    errors += 1
                    messages.append(f"{csv_file.name}: {str(e)}")

        elif 'system' in file_name or 'систем' in file_name:
            for row in rows:
                try:
                    import_system_from_dict(row)
                    success += 1
                except Exception as e:
                    errors += 1
                    messages.append(f"{csv_file.name}: {str(e)}")

        elif 'level' in file_name or 'уровень' in file_name:
            for row in rows:
                try:
                    import_level_from_dict(row)
                    success += 1
                except Exception as e:
                    errors += 1
                    messages.append(f"{csv_file.name}: {str(e)}")

        elif 'project' in file_name or 'проект' in file_name:
            for row in rows:
                try:
                    import_project_from_dict(row)
                    success += 1
                except Exception as e:
                    errors += 1
                    messages.append(f"{csv_file.name}: {str(e)}")

        else:
            # Определяем тип по содержимому
            first_row = rows[0]
            if 'inn' in first_row or 'ИНН' in first_row:
                for row in rows:
                    try:
                        import_participant_from_dict(row)
                        success += 1
                    except Exception:
                        errors += 1
            elif 'hierarchy_level' in first_row or 'Уровень' in first_row:
                for row in rows:
                    try:
                        import_object_from_dict(row)
                        success += 1
                    except Exception:
                        errors += 1
            elif 'system_class' in first_row or 'Класс' in first_row:
                for row in rows:
                    try:
                        import_system_from_dict(row)
                        success += 1
                    except Exception:
                        errors += 1

    except Exception as e:
        errors += 1
        messages.append(f"Ошибка в {csv_file.name}: {str(e)}")

    return success, errors, messages


# =============================================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ ИМПОРТА
# =============================================================================


def import_participant_item(data):
    """Импорт одного участника из словаря"""
    participant, _ = Participant.objects.update_or_create(
        inn=data.get('inn') or data.get('ИНН'),
        defaults={
            'name': (
                data.get('name')
                or data.get('название')
                or data.get('Название')
            ),
            'participant_type': (
                data.get('participant_type')
                or data.get('тип')
                or data.get('Тип')
            ),
            'is_partner': (
                data.get('is_partner')
                or data.get('partner')
                or data.get('Партнер') in ['Да', 'True', True]
            ),
            'website': data.get('website') or data.get('сайт') or data.get('Сайт'),
            'kam_name': data.get('kam_name') or data.get('кам') or data.get('КАМ'),
            'kam_phone': (
                data.get('kam_phone')
                or data.get('телефон кам')
                or data.get('Телефон КАМ')
            ),
        }
    )
    return participant


def import_participant_from_dict(row):
    """Импорт участника из CSV строки"""
    data = {k.lower().strip(): v for k, v in row.items()}
    inn = data.get('инн') or data.get('inn')
    if not inn:
        raise Exception("Отсутствует ИНН")

    participant, _ = Participant.objects.update_or_create(
        inn=inn.strip(),
        defaults={
            'name': data.get('название') or data.get('name') or '',
            'participant_type': (
                data.get('тип')
                or data.get('type')
                or data.get('participant_type')
                or 'VENDOR'
            ),
            'is_partner': (data.get('партнер') or data.get('partner') or '').lower()
            in ['да', 'yes', 'true', '1'],
            'website': data.get('сайт') or data.get('website') or '',
            'kam_name': data.get('кам') or data.get('kam') or data.get('kam_name') or '',
            'kam_phone': (
                data.get('телефон кам')
                or data.get('kam_phone')
                or ''
            ),
        }
    )
    return participant


def import_object_item(data):
    """Импорт одного объекта из словаря"""
    legal_entity_name = data.get('legal_entity') or data.get('юрлицо')
    legal_entity = None
    if legal_entity_name:
        legal_entity = LegalEntity.objects.filter(
            name__icontains=legal_entity_name
        ).first()

    address = None
    address_str = data.get('address') or data.get('адрес')
    if address_str and isinstance(address_str, str):
        parts = [p.strip() for p in address_str.split(',')]
        if len(parts) >= 3:
            address, _ = Address.objects.get_or_create(
                country='Россия',
                city=parts[0],
                street=parts[1] if len(parts) > 1 else '',
                house=parts[2] if len(parts) > 2 else '',
            )
    if not address:
        address = Address.objects.first()

    object_class_name = data.get('object_class') or data.get('класс')
    object_class = None
    if object_class_name:
        object_class = ObjectClass.objects.filter(
            name__icontains=object_class_name
        ).first()

    obj = Object.objects.create(
        name=data.get('name') or data.get('название') or '',
        short_name=data.get('short_name') or data.get('короткое имя') or '',
        hierarchy_level=(
            data.get('hierarchy_level')
            or data.get('уровень')
            or 'LEVEL_1'
        ),
        object_class=object_class,
        technology=data.get('technology') or data.get('технология') or '',
        category=data.get('category') or data.get('категория') or 'MAIN',
        start_year=int(
            data.get('start_year') or data.get('год ввода') or 2024
        ),
        capacity=float(data.get('capacity') or data.get('мощность') or 0),
        status=data.get('status') or data.get('статус') or 'ACTIVE',
        address=address,
        legal_entity=legal_entity,
    )
    return obj


def import_object_from_dict(row):
    """Импорт объекта из CSV строки"""
    data = {k.lower().strip(): v for k, v in row.items()}

    legal_entity_name = data.get('юрлицо') or data.get('legal_entity')
    legal_entity = None
    if legal_entity_name:
        legal_entity = LegalEntity.objects.filter(
            name__icontains=legal_entity_name
        ).first()

    address = None
    address_str = data.get('адрес') or data.get('address')
    if address_str:
        parts = [p.strip() for p in address_str.split(',')]
        if len(parts) >= 3:
            address, _ = Address.objects.get_or_create(
                country='Россия',
                city=parts[0],
                street=parts[1],
                house=parts[2],
            )
    if not address:
        address = Address.objects.first()

    object_class_name = data.get('класс') or data.get('class')
    object_class = None
    if object_class_name:
        object_class = ObjectClass.objects.filter(
            name__icontains=object_class_name
        ).first()

    obj = Object.objects.create(
        name=data.get('название') or data.get('name') or '',
        short_name=data.get('короткое имя') or data.get('short_name') or '',
        hierarchy_level=(
            data.get('уровень')
            or data.get('level')
            or 'LEVEL_1'
        ),
        object_class=object_class,
        technology=data.get('технология') or data.get('technology') or '',
        category=data.get('категория') or data.get('category') or 'MAIN',
        start_year=int(
            data.get('год ввода') or data.get('start_year') or 2024
        ),
        capacity=float(data.get('мощность') or data.get('capacity') or 0),
        status=data.get('статус') or data.get('status') or 'ACTIVE',
        address=address,
        legal_entity=legal_entity,
    )
    return obj


def import_system_item(data):
    """Импорт одной системы из словаря"""
    object_name = data.get('object') or data.get('объект')
    object_obj = None
    if object_name:
        object_obj = Object.objects.filter(
            name__icontains=object_name
        ).first()

    vendor_name = data.get('vendor') or data.get('вендор')
    vendor = None
    if vendor_name:
        vendor = Participant.objects.filter(
            name__icontains=vendor_name
        ).first()

    integrator_name = data.get('integrator') or data.get('интегратор')
    integrator = None
    if integrator_name:
        integrator = Participant.objects.filter(
            name__icontains=integrator_name
        ).first()

    system = AutomatedSystem.objects.create(
        name=data.get('name') or data.get('название') or '',
        system_class=(
            data.get('system_class')
            or data.get('класс')
            or 'DCS'
        ),
        object=object_obj,
        vendor=vendor,
        integrator=integrator,
        status=data.get('status') or data.get('статус') or 'ACTIVE',
        version=data.get('version') or data.get('версия') or '',
    )
    return system


def import_system_from_dict(row):
    """Импорт системы из CSV строки"""
    data = {k.lower().strip(): v for k, v in row.items()}

    object_name = data.get('объект') or data.get('object')
    object_obj = None
    if object_name:
        object_obj = Object.objects.filter(
            name__icontains=object_name
        ).first()

    vendor_name = data.get('вендор') or data.get('vendor')
    vendor = None
    if vendor_name:
        vendor = Participant.objects.filter(
            name__icontains=vendor_name
        ).first()

    integrator_name = data.get('интегратор') or data.get('integrator')
    integrator = None
    if integrator_name:
        integrator = Participant.objects.filter(
            name__icontains=integrator_name
        ).first()

    system = AutomatedSystem.objects.create(
        name=data.get('название') or data.get('name') or '',
        system_class=(
            data.get('класс')
            or data.get('system_class')
            or 'DCS'
        ),
        object=object_obj,
        vendor=vendor,
        integrator=integrator,
        status=data.get('статус') or data.get('status') or 'ACTIVE',
        version=data.get('версия') or data.get('version') or '',
    )
    return system


def import_level_item(data):
    """Импорт уровня автоматизации из словаря"""
    object_name = data.get('object') or data.get('объект')
    object_obj = None
    if object_name:
        object_obj = Object.objects.filter(
            name__icontains=object_name
        ).first()

    level_code = data.get('level') or data.get('уровень')
    level = None
    if level_code:
        level = AutomationLevel.objects.filter(
            code=level_code.upper()
        ).first()

    if object_obj and level:
        obj_level, _ = ObjectAutomationLevel.objects.update_or_create(
            object=object_obj,
            level=level,
            defaults={
                'status': (
                    data.get('status')
                    or data.get('статус')
                    or 'PLANNED'
                ),
                'implementation_year': int(
                    data.get('year') or data.get('год') or 2024
                ),
            }
        )
        return obj_level
    return None


def import_level_from_dict(row):
    """Импорт уровня из CSV строки"""
    data = {k.lower().strip(): v for k, v in row.items()}

    object_name = data.get('объект') or data.get('object')
    level_code = data.get('уровень') or data.get('level')

    if not object_name or not level_code:
        raise Exception("Не указан объект или уровень")

    object_obj = Object.objects.filter(
        name__icontains=object_name
    ).first()
    level = AutomationLevel.objects.filter(
        code=level_code.upper()
    ).first()

    if not object_obj:
        raise Exception(f"Объект '{object_name}' не найден")
    if not level:
        raise Exception(f"Уровень '{level_code}' не найден")

    obj_level, _ = ObjectAutomationLevel.objects.update_or_create(
        object=object_obj,
        level=level,
        defaults={
            'status': (
                data.get('статус')
                or data.get('status')
                or 'COMPLETED'
            ),
            'implementation_year': int(
                data.get('год') or data.get('year') or 2024
            ),
        }
    )
    return obj_level


def import_project_from_dict(row):
    """Импорт проекта из CSV строки"""
    data = {k.lower().strip(): v for k, v in row.items()}

    participant_name = data.get('участник') or data.get('participant')
    object_name = data.get('объект') or data.get('object')

    participant = None
    if participant_name:
        participant = Participant.objects.filter(
            name__icontains=participant_name
        ).first()

    object_obj = None
    if object_name:
        object_obj = Object.objects.filter(
            name__icontains=object_name
        ).first()

    project, _ = Project.objects.update_or_create(
        name=data.get('название') or data.get('name') or '',
        defaults={
            'participant': participant,
            'object': object_obj,
            'year': int(data.get('год') or data.get('year') or 2024),
            'successful': (
                data.get('успешно') or ''
            ).lower() in ['да', 'yes', 'true', '1'],
            'description': (
                data.get('описание')
                or data.get('description')
                or ''
            ),
        }
    )
    return project


# =============================================================================
# СТРАНИЦЫ
# =============================================================================

@login_required
@viewer_required
def export_import_page(request):
    """Страница управления импортом/экспортом"""
    return render(request, 'export_import.html')


@login_required
@viewer_required
def ownership_view(request):
    """Отображение структуры собственности"""
    from django.db.models import Prefetch

    groups = CompanyGroup.objects.prefetch_related(
        Prefetch(
            'legalentity_set',
            queryset=LegalEntity.objects.prefetch_related(
                Prefetch(
                    'object_set',
                    queryset=Object.objects.select_related('object_class')
                )
            )
        )
    ).all()

    return render(request, 'ownership_tree.html', {'groups': groups})


def overview_view(request):
    """Главная страница со статистикой (доступна всем)"""
    try:
        total_objects = Object.objects.count()
        total_participants = Participant.objects.count()
        total_systems = AutomatedSystem.objects.count()
        total_classes = ObjectClass.objects.count()

        recent_objects = Object.objects.all().select_related(
            'object_class'
        ).order_by('-id')[:10]

    except Exception as e:
        total_objects = total_participants = total_systems = total_classes = 0
        recent_objects = []
        print(f"Ошибка БД в overview_view: {e}")

    context = {
        'total_objects': total_objects or 0,
        'total_participants': total_participants or 0,
        'total_systems': total_systems or 0,
        'total_classes': total_classes or 0,
        'recent_objects': recent_objects or [],
    }

    return render(request, 'overview.html', context)


# =============================================================================
# ОБЪЕКТЫ
# =============================================================================

@login_required
@viewer_required
def object_list_view(request):
    """Список всех объектов с фильтрацией и поиском"""
    base_queryset = Object.objects.select_related(
        'legal_entity', 'legal_entity__group', 'object_class', 'address', 'parent', 'created_by'
    ).prefetch_related('automated_systems')

    level_filter = request.GET.get('level')
    category_filter = request.GET.get('category')
    search_query = request.GET.get('q')

    filtered_objects = base_queryset

    if search_query:
        filtered_objects = _apply_search_filter(base_queryset, search_query)

    if level_filter:
        filtered_objects = filtered_objects.filter(hierarchy_level=level_filter)

    if category_filter:
        filtered_objects = filtered_objects.filter(category=category_filter)

    active_count = filtered_objects.filter(status='ACTIVE').count()
    level1_count = filtered_objects.filter(hierarchy_level='LEVEL_1').count()
    vendors_count = Participant.objects.filter(
        automated_systems_vendor__object__in=filtered_objects
    ).distinct().count()

    paginator = Paginator(filtered_objects, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'hierarchy_levels': Object.HIERARCHY_LEVELS,
        'categories': Object.CATEGORIES,
        'filters': {
            'level': level_filter,
            'category': category_filter,
            'q': search_query,
        },
        'active_count': active_count,
        'level1_count': level1_count,
        'vendors_count': vendors_count,
        'can_create': request.user.groups.filter(name='Редакторы').exists() or request.user.is_superuser,
    }

    return render(request, 'object_list.html', context)


def _apply_search_filter(queryset, search_query):
    """Применяет поиск с исправлением опечаток"""
    corrections = {
        'мзпн': 'мнпз',
        'омзп': 'онпз',
        'нзп': 'нпз',
        'авь': 'авт',
        'г-43-170': 'г-43-107',
        'г43170': 'г-43-107',
        'лч3511': 'лч-35-11',
    }

    corrected_query = corrections.get(search_query, search_query)

    parent_objects = queryset.filter(
        Q(name__icontains=corrected_query) |
        Q(short_name__icontains=corrected_query) |
        Q(legal_entity__name__icontains=corrected_query),
        hierarchy_level='LEVEL_1'
    )

    if parent_objects.exists():
        parent_ids = [obj.id for obj in parent_objects]
        all_related_ids = set(parent_ids)

        def collect_all_descendants(ids):
            children = queryset.filter(parent_id__in=ids).values_list('id', flat=True)
            if children:
                child_ids = list(children)
                all_related_ids.update(child_ids)
                collect_all_descendants(child_ids)

        collect_all_descendants(parent_ids)
        return queryset.filter(id__in=all_related_ids)

    exact_matches = queryset.filter(
        Q(name__icontains=corrected_query) |
        Q(short_name__icontains=corrected_query) |
        Q(technology__icontains=corrected_query) |
        Q(legal_entity__name__icontains=corrected_query)
    )

    if exact_matches.exists():
        return exact_matches

    return queryset.none()


@login_required
@viewer_required
def object_detail_view(request, object_id):
    """Детальная информация об объекте"""
    obj = get_object_or_404(
        Object.objects.select_related(
            'legal_entity', 'object_class', 'address', 'parent', 'created_by'
        ).prefetch_related(
            'automated_systems',
            'automated_systems__vendor',
            'automated_systems__integrator',
            'automated_systems__implementer',
            'automated_systems__vendor_product',
            'automation_levels',
            'automation_levels__level',
            'characteristic_values',
            'characteristic_values__characteristic',
        ),
        id=object_id
    )

    hierarchy = []
    current = obj
    while current:
        hierarchy.insert(0, current)
        current = current.parent

    children = obj.children.select_related('object_class').all()

    automation_summary = {
        'levels': [],
        'system_classes': set(),
        'vendors': set(),
        'integrators': set()
    }

    for obj_level in obj.automation_levels.select_related('level'):
        automation_summary['levels'].append({
            'level': obj_level.level,
            'status': obj_level.get_status_display(),
            'year': obj_level.implementation_year
        })

    for system in obj.automated_systems.all():
        if system.system_class:
            automation_summary['system_classes'].add(
                system.get_system_class_display()
            )
        automation_summary['vendors'].add(system.vendor)
        if system.integrator:
            automation_summary['integrators'].add(system.integrator)

    automation_matrix = get_automation_matrix_for_object(obj.id)

    context = {
        'object': obj,
        'hierarchy': hierarchy,
        'children': children,
        'automation_matrix': automation_matrix,
        'automation_levels': obj.automation_levels.all(),
        'characteristics': obj.characteristic_values.all(),
        'systems': obj.automated_systems.all(),
        'automation_summary': automation_summary,
        'can_edit': obj.can_edit(request.user),
        'can_delete': obj.can_delete(request.user),
    }

    return render(request, 'object_detail.html', context)


@login_required
@editor_required
def object_create_view(request):
    """Создание нового объекта"""
    if request.method == 'POST':
        form = ObjectForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.created_by = request.user
            obj.save()
            messages.success(request, f'Объект "{obj.name}" успешно создан!')
            return redirect('object_detail', obj.id)
    else:
        form = ObjectForm()

    return render(request, 'object_form.html', {
        'form': form,
        'title': 'Создание объекта'
    })


@login_required
def object_edit_view(request, pk):
    """Редактирование объекта"""
    obj = get_object_or_404(Object, pk=pk)

    # Проверка прав
    if not obj.can_edit(request.user):
        messages.error(request, 'У вас нет прав для редактирования этого объекта')
        return redirect('object_detail', pk)

    if request.method == 'POST':
        form = ObjectForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, f'Объект "{obj.name}" успешно обновлен!')
            return redirect('object_detail', pk)
    else:
        form = ObjectForm(instance=obj)

    return render(request, 'object_form.html', {
        'form': form,
        'object': obj,
        'title': f'Редактирование: {obj.name}'
    })


@login_required
def object_delete_view(request, pk):
    """Удаление объекта"""
    obj = get_object_or_404(Object, pk=pk)

    if not obj.can_delete(request.user):
        messages.error(request, 'Только администратор может удалять объекты')
        return redirect('object_detail', pk)

    if request.method == 'POST':
        obj.delete()
        messages.success(request, f'Объект "{obj.name}" удален')
        return redirect('object_list')

    return render(request, 'object_confirm_delete.html', {'object': obj})


# =============================================================================
# УЧАСТНИКИ
# =============================================================================

@login_required
@viewer_required
def participant_list_view(request):
    """Традиционный список участников с оптимизированной статистикой"""
    participants = Participant.objects.annotate(
        vendor_count=Count('automated_systems_vendor', distinct=True),
        integrator_count=Count('automated_systems_integrator', distinct=True),
        implementer_count=Count('automated_systems_implementer', distinct=True),
    ).order_by('name')

    all_participants = Participant.objects.all()

    type_filter = request.GET.get('type')
    partner_filter = request.GET.get('partner')
    search_query = request.GET.get('q')

    if type_filter:
        participants = participants.filter(participant_type=type_filter)
    if partner_filter:
        participants = participants.filter(
            is_partner=(partner_filter == 'true')
        )
    if search_query:
        participants = participants.filter(
            Q(name__icontains=search_query) |
            Q(profile__icontains=search_query) |
            Q(inn__icontains=search_query)
        )

    paginator = Paginator(participants, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    vendor_count = all_participants.filter(participant_type='VENDOR').count()
    engineering_count = all_participants.filter(
        participant_type='ENGINEERING'
    ).count()
    supplier_count = all_participants.filter(participant_type='SUPPLIER').count()
    full_cycle_count = all_participants.filter(
        participant_type='FULL_CYCLE'
    ).count()

    total_projects = Project.objects.count()

    context = {
        'participants': page_obj.object_list,
        'page_obj': page_obj,
        'participant_types': Participant.PARTICIPANT_TYPES,
        'filters': {
            'type': type_filter,
            'partner': partner_filter,
            'q': search_query,
        },
        'total_count': participants.count(),
        'vendor_count': vendor_count,
        'engineering_count': engineering_count,
        'supplier_count': supplier_count,
        'full_cycle_count': full_cycle_count,
        'total_projects': total_projects,
        'can_create': request.user.groups.filter(name='Редакторы').exists() or request.user.is_superuser,
    }

    return render(request, 'participant_list.html', context)


@login_required
@viewer_required
def participant_detail_view(request, participant_id):
    """Детальная информация об участнике"""
    participant = get_object_or_404(
        Participant.objects.select_related('created_by').prefetch_related(
            'vendor_products',
            'projects',
            'certificates',
            'reviews',
            'tco_analyses',
        ),
        id=participant_id
    )

    all_systems = AutomatedSystem.objects.filter(
        Q(vendor=participant) |
        Q(implementer=participant) |
        Q(integrator=participant)
    ).select_related(
        'object',
        'object__legal_entity',
        'object__parent',
        'object__parent__parent',
        'level',
        'vendor_product'
    )

    all_objects_dict = {}
    for system in all_systems:
        if system.object:
            obj = system.object
            all_objects_dict[obj.id] = obj
            parent = obj.parent
            while parent:
                all_objects_dict[parent.id] = parent
                parent = parent.parent

    unique_objects = list(all_objects_dict.values())
    clients_hierarchy = _build_clients_hierarchy(unique_objects, all_systems)

    formatted_clients = _format_clients_hierarchy(clients_hierarchy)

    vendor_products = participant.vendor_products.all()
    projects = participant.projects.all().select_related(
        'object', 'vendor_product'
    )[:10]
    certificates = participant.certificates.all().order_by('-issued_date')[:10]
    reviews = participant.reviews.all().order_by('-date')[:10]
    tco_analyses = participant.tco_analyses.all().select_related('vendor_product')

    for tco in tco_analyses:
        tco.total = tco.total_tco()

    context = {
        'participant': participant,
        'clients': formatted_clients,
        'vendor_products': vendor_products,
        'total_objects': len(unique_objects),
        'total_clients': len(clients_hierarchy),
        'projects': projects,
        'certificates': certificates,
        'reviews': reviews,
        'tco_analyses': tco_analyses,
        'has_f2_data': any([
            projects.exists(),
            certificates.exists(),
            reviews.exists(),
            tco_analyses.exists()
        ]),
        'can_edit': participant.can_edit(request.user),
        'can_delete': participant.can_delete(request.user),
    }

    return render(request, 'participant_detail.html', context)


@login_required
@editor_required
def participant_create_view(request):
    """Создание нового участника"""
    if request.method == 'POST':
        form = ParticipantForm(request.POST)
        if form.is_valid():
            participant = form.save(commit=False)
            participant.created_by = request.user
            participant.save()
            messages.success(request, f'Участник "{participant.name}" успешно создан!')
            return redirect('participant_detail', participant.id)
    else:
        form = ParticipantForm()

    return render(request, 'participant_form.html', {
        'form': form,
        'title': 'Создание участника'
    })


@login_required
def participant_edit_view(request, pk):
    """Редактирование участника"""
    participant = get_object_or_404(Participant, pk=pk)

    if not participant.can_edit(request.user):
        messages.error(request, 'У вас нет прав для редактирования этого участника')
        return redirect('participant_detail', pk)

    if request.method == 'POST':
        form = ParticipantForm(request.POST, instance=participant)
        if form.is_valid():
            form.save()
            messages.success(request, f'Участник "{participant.name}" успешно обновлен!')
            return redirect('participant_detail', pk)
    else:
        form = ParticipantForm(instance=participant)

    return render(request, 'participant_form.html', {
        'form': form,
        'object': participant,
        'title': f'Редактирование: {participant.name}'
    })


@login_required
def participant_delete_view(request, pk):
    """Удаление участника"""
    participant = get_object_or_404(Participant, pk=pk)

    if not participant.can_delete(request.user):
        messages.error(request, 'Только администратор может удалять участников')
        return redirect('participant_detail', pk)

    if request.method == 'POST':
        participant.delete()
        messages.success(request, f'Участник "{participant.name}" удален')
        return redirect('participant_list')

    return render(request, 'participant_confirm_delete.html', {'object': participant})


# =============================================================================
# АВТОМАТИЗИРОВАННЫЕ СИСТЕМЫ
# =============================================================================

@login_required
@viewer_required
def system_list_view(request):
    """Список автоматизированных систем с фильтрацией"""
    all_systems = AutomatedSystem.objects.select_related(
        'object', 'vendor', 'integrator', 'implementer', 'level', 'vendor_product', 'created_by'
    ).order_by('-installation_date', '-created_at')

    system_class_filter = request.GET.get('system_class')
    status_filter = request.GET.get('status')
    level_filter = request.GET.get('level')
    vendor_filter = request.GET.get('vendor')
    search_query = request.GET.get('q')

    if system_class_filter:
        all_systems = all_systems.filter(system_class=system_class_filter)
    if status_filter:
        all_systems = all_systems.filter(status=status_filter)
    if level_filter:
        all_systems = all_systems.filter(level__code=level_filter)
    if vendor_filter:
        all_systems = all_systems.filter(vendor_id=vendor_filter)
    if search_query:
        all_systems = all_systems.filter(
            Q(name__icontains=search_query) |
            Q(object__name__icontains=search_query) |
            Q(vendor__name__icontains=search_query) |
            Q(vendor_product__name__icontains=search_query)
        )

    paginator = Paginator(all_systems, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    vendors = Participant.objects.filter(
        Q(automated_systems_vendor__isnull=False) |
        Q(automated_systems_integrator__isnull=False)
    ).distinct().order_by('name')

    system_types_count = all_systems.values('system_class').distinct().count()

    context = {
        'page_obj': page_obj,
        'all_systems': all_systems,
        'systems': page_obj.object_list,
        'system_classes': SYSTEM_CLASSES,
        'status_choices': AutomatedSystem.STATUS_CHOICES,
        'levels': AutomationLevel.objects.all().order_by('order'),
        'vendors': vendors,
        'system_types_count': system_types_count,
        'filters': {
            'system_class': system_class_filter,
            'status': status_filter,
            'level': level_filter,
            'vendor': vendor_filter,
            'q': search_query,
        },
        'can_create': request.user.groups.filter(name='Редакторы').exists() or request.user.is_superuser,
    }

    return render(request, 'system_list.html', context)


@login_required
@viewer_required
def system_detail_view(request, pk):
    """Детальная информация об автоматизированной системе"""
    system = get_object_or_404(
        AutomatedSystem.objects.select_related(
            'object',
            'object__legal_entity',
            'object__object_class',
            'level',
            'vendor',
            'integrator',
            'implementer',
            'vendor_product',
            'created_by'
        ).prefetch_related(
            'object__parent',
            'object__children'
        ),
        pk=pk
    )

    other_systems = AutomatedSystem.objects.filter(
        object=system.object
    ).exclude(
        pk=system.pk
    ).select_related(
        'level', 'vendor', 'vendor_product'
    )[:5]

    product_stats = None
    if system.vendor_product:
        product_stats = {
            'product': system.vendor_product,
            'total_implementations': AutomatedSystem.objects.filter(
                vendor_product=system.vendor_product
            ).count(),
            'total_clients': AutomatedSystem.objects.filter(
                vendor_product=system.vendor_product
            ).values('object__legal_entity').distinct().count()
        }

    context = {
        'system': system,
        'other_systems': other_systems,
        'product_stats': product_stats,
        'can_edit': system.can_edit(request.user),
        'can_delete': system.can_delete(request.user),
    }

    return render(request, 'system_detail.html', context)


@login_required
@editor_required
def system_create_view(request):
    """Создание новой системы"""
    if request.method == 'POST':
        form = AutomatedSystemForm(request.POST)
        if form.is_valid():
            system = form.save(commit=False)
            system.created_by = request.user
            system.save()
            messages.success(request, f'Система "{system.name}" успешно создана!')
            return redirect('automated_system_detail', system.id)
    else:
        form = AutomatedSystemForm()

    return render(request, 'system_form.html', {
        'form': form,
        'title': 'Создание системы'
    })


@login_required
def system_edit_view(request, pk):
    """Редактирование системы"""
    system = get_object_or_404(AutomatedSystem, pk=pk)

    if not system.can_edit(request.user):
        messages.error(request, 'У вас нет прав для редактирования этой системы')
        return redirect('automated_system_detail', pk)

    if request.method == 'POST':
        form = AutomatedSystemForm(request.POST, instance=system)
        if form.is_valid():
            form.save()
            messages.success(request, f'Система "{system.name}" успешно обновлена!')
            return redirect('automated_system_detail', pk)
    else:
        form = AutomatedSystemForm(instance=system)

    return render(request, 'system_form.html', {
        'form': form,
        'object': system,
        'title': f'Редактирование: {system.name}'
    })


@login_required
def system_delete_view(request, pk):
    """Удаление системы"""
    system = get_object_or_404(AutomatedSystem, pk=pk)

    if not system.can_delete(request.user):
        messages.error(request, 'Только администратор может удалять системы')
        return redirect('automated_system_detail', pk)

    if request.method == 'POST':
        system.delete()
        messages.success(request, f'Система "{system.name}" удалена')
        return redirect('system_list')

    return render(request, 'system_confirm_delete.html', {'object': system})


# =============================================================================
# КЛАССЫ
# =============================================================================

@login_required
@viewer_required
def class_list_view(request):
    """Список классов объектов"""
    classes_list = ObjectClass.objects.annotate(
        object_count=Count('objects_in_class')
    ).order_by('name')

    context = {
        'classes': classes_list,
    }

    return render(request, 'class_list.html', context)


@login_required
@viewer_required
def class_detail_view(request, class_id):
    """Детальная информация о классе объектов"""
    class_obj = get_object_or_404(ObjectClass, id=class_id)
    objects = Object.objects.filter(
        object_class=class_obj
    ).select_related('legal_entity', 'parent')

    total_objects = objects.count()
    object_types = objects.values('technology', 'category').distinct().count()

    total_vendors = Participant.objects.filter(
        automated_systems_vendor__object__object_class=class_obj
    ).distinct().count()

    system_types = AutomatedSystem.objects.filter(
        object__object_class=class_obj
    ).values('system_class').distinct().count()

    tables_data = {}
    for level_code, level_name in Object.HIERARCHY_LEVELS:
        level_objects = objects.filter(hierarchy_level=level_code)

        table_objects = []
        for obj in level_objects[:4]:
            industry = obj.legal_entity.name if obj.legal_entity else '-'
            top_parent = obj.get_top_level_parent()

            table_objects.append({
                'id': obj.id,
                'name': obj.name,
                'industry': industry,
                'category': obj.get_category_display(),
                'top_parent': (
                    top_parent.name
                    if top_parent and top_parent != obj
                    else '-'
                ),
                'info_url': f'/objects/{obj.id}/',
            })

        tables_data[level_code] = {
            'objects': table_objects,
            'total_count': level_objects.count(),
            'has_more': level_objects.count() > 4,
        }

    characteristics = class_obj.characteristics.all()
    requirements = class_obj.automation_requirements.select_related('level').all()

    context = {
        'class': class_obj,
        'total_objects': total_objects,
        'object_types_count': object_types,
        'total_vendors': total_vendors,
        'system_types_count': system_types,
        'tables_data': tables_data,
        'hierarchy_levels': Object.HIERARCHY_LEVELS,
        'characteristics': characteristics,
        'requirements': requirements,
    }

    return render(request, 'class_detail.html', context)


@login_required
@viewer_required
def class_hierarchy_view(request):
    """Иерархия классов - древовидное представление"""
    root_classes = ObjectClass.objects.filter(parent__isnull=True)

    def build_hierarchy(class_obj, level=0):
        children = ObjectClass.objects.filter(parent=class_obj)
        object_count = class_obj.objects_in_class.count()

        hierarchy = {
            'id': class_obj.id,
            'name': class_obj.name,
            'code': class_obj.code,
            'description': class_obj.description,
            'level': level,
            'object_count': object_count,
            'parent': class_obj.parent,
            'children': [build_hierarchy(child, level + 1) for child in children]
        }
        return hierarchy

    hierarchy = [build_hierarchy(root) for root in root_classes]

    flat_hierarchy = []

    def flatten_hierarchy(hier, level=0):
        for item in hier:
            flat_hierarchy.append({
                'id': item['id'],
                'name': item['name'],
                'code': item['code'],
                'description': item['description'],
                'level': level,
                'object_count': item['object_count'],
                'parent': item['parent']
            })
            if item['children']:
                flatten_hierarchy(item['children'], level + 1)

    flatten_hierarchy(hierarchy)

    total_classes = ObjectClass.objects.count()
    root_classes_count = root_classes.count()
    child_classes_count = total_classes - root_classes_count
    total_objects = Object.objects.count()

    context = {
        'hierarchy': hierarchy,
        'flat_hierarchy': flat_hierarchy,
        'total_classes': total_classes,
        'root_classes': root_classes_count,
        'child_classes': child_classes_count,
        'total_objects': total_objects,
    }

    return render(request, 'class_hierarchy.html', context)


# =============================================================================
# ВЕНДОРСКИЕ ПРОДУКТЫ
# =============================================================================

@login_required
@viewer_required
def vendor_product_list_view(request):
    """Список вендорских продуктов"""
    products = VendorProduct.objects.select_related('vendor', 'created_by').annotate(
        implementation_count=Count('automated_systems'),
        client_count=Count(
            'automated_systems__object__legal_entity',
            distinct=True
        )
    ).order_by('vendor__name', 'name')

    vendor_filter = request.GET.get('vendor')
    product_type_filter = request.GET.get('type')
    search_query = request.GET.get('q')

    if vendor_filter:
        products = products.filter(vendor_id=vendor_filter)
    if product_type_filter:
        products = products.filter(product_type=product_type_filter)
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(code__icontains=search_query) |
            Q(vendor__name__icontains=search_query)
        )

    vendors = Participant.objects.filter(
        participant_type__in=['VENDOR', 'FULL_CYCLE']
    ).order_by('name')

    context = {
        'products': products,
        'vendors': vendors,
        'product_types': VendorProduct.PRODUCT_TYPE_CHOICES,
        'filters': {
            'vendor': vendor_filter,
            'type': product_type_filter,
            'q': search_query,
        },
        'can_create': request.user.groups.filter(name='Редакторы').exists() or request.user.is_superuser,
    }

    return render(request, 'vendor_products_list.html', context)


@login_required
@viewer_required
def vendor_product_detail_view(request, product_id):
    """Детальная информация о вендорском продукте"""
    product = get_object_or_404(
        VendorProduct.objects.select_related('vendor', 'created_by'),
        id=product_id
    )

    systems = AutomatedSystem.objects.filter(
        vendor_product=product
    ).select_related(
        'object', 'level', 'vendor', 'integrator', 'implementer'
    ).all()

    clients = []
    client_ids = set()

    for system in systems:
        if system.object and system.object.legal_entity:
            client_id = system.object.legal_entity.id
            if client_id not in client_ids:
                client_ids.add(client_id)
                object_count = AutomatedSystem.objects.filter(
                    vendor_product=product,
                    object__legal_entity=system.object.legal_entity
                ).count()

                clients.append({
                    'id': system.object.legal_entity.id,
                    'name': system.object.legal_entity.name,
                    'inn': system.object.legal_entity.inn,
                    'object_count': object_count
                })

    implementation_count = systems.count()
    client_count = len(clients)

    system_classes = list(set(
        system.get_system_class_display()
        for system in systems
        if system.system_class
    ))

    industries = set()
    for system in systems:
        if (
            system.object
            and system.object.legal_entity
            and system.object.legal_entity.name
        ):
            industries.add(system.object.legal_entity.name)

    context = {
        'product': product,
        'clients': clients,
        'systems': systems,
        'implementation_count': implementation_count,
        'client_count': client_count,
        'system_classes': system_classes,
        'industries': list(industries)[:5],
        'can_edit': product.can_edit(request.user),
        'can_delete': product.can_delete(request.user),
    }

    return render(request, 'vendor_product_detail.html', context)


# =============================================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# =============================================================================

def get_automation_matrix_for_object(object_id):
    """Возвращает матрицу автоматизации объекта по уровням L0-L4"""
    levels = AutomationLevel.objects.all().order_by('order')
    matrix = []

    for level in levels:
        obj_level = ObjectAutomationLevel.objects.filter(
            object_id=object_id,
            level=level
        ).first()

        systems = AutomatedSystem.objects.filter(
            object_id=object_id,
            level=level
        ).select_related('vendor', 'integrator', 'vendor_product')

        system_info = []
        for system in systems:
            system_info.append({
                'id': system.id,
                'name': system.name,
                'system_class': system.get_system_class_display(),
                'vendor': system.vendor,
                'integrator': system.integrator,
                'vendor_product': system.vendor_product,
                'status': system.get_status_display(),
                'installation_date': system.installation_date,
            })

        status = 'NOT_IMPLEMENTED'
        status_display = 'Не реализован'
        status_color = 'light'
        implementation_year = None

        if obj_level:
            status = obj_level.status
            status_display = obj_level.get_status_display()
            implementation_year = obj_level.implementation_year

            status_colors = {
                'PLANNED': 'secondary',
                'IN_PROGRESS': 'warning',
                'COMPLETED': 'success',
                'PARTIAL': 'info',
            }
            status_color = status_colors.get(status, 'light')

        matrix.append({
            'level': level,
            'status': status,
            'status_display': status_display,
            'status_color': status_color,
            'implementation_year': implementation_year,
            'systems': system_info,
            'system_count': len(systems),
            'classes': [s.get_system_class_display() for s in systems],
        })

    return matrix


def _build_clients_hierarchy(unique_objects, all_systems):
    """Строит иерархию клиентов для participant_detail_view"""
    clients_hierarchy = {}

    for obj in unique_objects:
        if not obj.legal_entity:
            continue

        client_id = obj.legal_entity.id

        if client_id not in clients_hierarchy:
            clients_hierarchy[client_id] = {
                'client': obj.legal_entity,
                'level1_objects': {},
                'system_count': 0,
                'system_classes': set()
            }

        client_data = clients_hierarchy[client_id]

        if obj.hierarchy_level == 'LEVEL_1':
            if obj.id not in client_data['level1_objects']:
                client_data['level1_objects'][obj.id] = {
                    'object': obj,
                    'children': {},
                    'direct_systems': [],
                    'level2_systems': [],
                    'level3_systems': [],
                    'total_systems': 0
                }

    for obj in unique_objects:
        if not obj.legal_entity or obj.hierarchy_level == 'LEVEL_1':
            continue

        client_id = obj.legal_entity.id
        if client_id not in clients_hierarchy:
            continue

        client_data = clients_hierarchy[client_id]
        top_parent = obj.get_top_level_parent()

        if top_parent and top_parent.id in client_data['level1_objects']:
            level1_obj = client_data['level1_objects'][top_parent.id]

            if obj.hierarchy_level == 'LEVEL_2':
                if obj.id not in level1_obj['children']:
                    level1_obj['children'][obj.id] = {
                        'object': obj,
                        'systems': [],
                        'children': {}
                    }
            elif obj.hierarchy_level == 'LEVEL_3':
                if obj.parent and obj.parent.hierarchy_level == 'LEVEL_2':
                    parent_level2_id = obj.parent.id
                    if parent_level2_id in level1_obj['children']:
                        if obj.id not in level1_obj['children'][parent_level2_id]['children']:
                            level1_obj['children'][parent_level2_id]['children'][obj.id] = {
                                'object': obj,
                                'systems': []
                            }

    for system in all_systems:
        obj = system.object
        if not obj or not obj.legal_entity:
            continue

        client_id = obj.legal_entity.id
        if client_id not in clients_hierarchy:
            continue

        client_data = clients_hierarchy[client_id]

        if system.system_class:
            client_data['system_classes'].add(system.system_class)

        client_data['system_count'] += 1

        top_parent = obj.get_top_level_parent()
        if not top_parent or top_parent.id not in client_data['level1_objects']:
            continue

        level1_obj = client_data['level1_objects'][top_parent.id]
        level1_obj['total_systems'] += 1

        if obj.hierarchy_level == 'LEVEL_1':
            level1_obj['direct_systems'].append(system)

        elif obj.hierarchy_level == 'LEVEL_2':
            if obj.id in level1_obj['children']:
                level1_obj['children'][obj.id]['systems'].append(system)
                if 'level2_systems' not in level1_obj:
                    level1_obj['level2_systems'] = []
                level1_obj['level2_systems'].append(system)

        elif obj.hierarchy_level == 'LEVEL_3':
            if obj.parent and obj.parent.hierarchy_level == 'LEVEL_2':
                parent_level2_id = obj.parent.id
                if parent_level2_id in level1_obj['children']:
                    if obj.id in level1_obj['children'][parent_level2_id]['children']:
                        level1_obj['children'][parent_level2_id]['children'][obj.id]['systems'].append(system)
                        if 'level3_systems' not in level1_obj:
                            level1_obj['level3_systems'] = []
                        level1_obj['level3_systems'].append(system)

    return clients_hierarchy


def _format_clients_hierarchy(clients_hierarchy):
    """Форматирует иерархию клиентов для шаблона"""
    formatted_clients = []

    for client_data in clients_hierarchy.values():
        level1_list = []
        for level1_id, level1_data in client_data['level1_objects'].items():
            children_list = []
            for child_id, child_data in level1_data['children'].items():
                grandchildren_list = []
                for grandchild_id, grandchild_data in child_data['children'].items():
                    grandchildren_list.append({
                        'object': grandchild_data['object'],
                        'systems': grandchild_data['systems']
                    })

                children_list.append({
                    'object': child_data['object'],
                    'systems': child_data['systems'],
                    'children': grandchildren_list
                })

            level1_list.append({
                'object': level1_data['object'],
                'direct_systems': level1_data.get('direct_systems', []),
                'level2_systems': level1_data.get('level2_systems', []),
                'level3_systems': level1_data.get('level3_systems', []),
                'children': children_list,
                'total_systems': level1_data['total_systems']
            })

        level1_list.sort(key=lambda x: x['total_systems'], reverse=True)

        formatted_clients.append({
            'client': client_data['client'],
            'level1_objects': level1_list,
            'total_systems': client_data['system_count'],
            'system_classes': list(client_data['system_classes'])
        })

    formatted_clients.sort(key=lambda x: x['total_systems'], reverse=True)
    return formatted_clients


# =============================================================================
# ОТЧЁТЫ И АНАЛИТИКА
# =============================================================================

@login_required
@viewer_required
def participants_by_type_view(request):
    """Участники сгруппированные по типам"""
    participants_by_type = {}
    total_counts = {
        'VENDOR': 0,
        'ENGINEERING': 0,
        'FULL_CYCLE': 0,
        'SUPPLIER': 0,
    }

    for p_type, p_label in Participant.PARTICIPANT_TYPES:
        participants = Participant.objects.filter(
            participant_type=p_type
        ).annotate(
            system_types_count=Count(
                'automated_systems_vendor__system_class',
                distinct=True
            ),
            client_count=Count(
                'automated_systems_vendor__object__legal_entity',
                distinct=True
            ),
            project_count=Count('automated_systems_vendor', distinct=True),
        ).order_by('name')

        participants_data = []
        for participant in participants:
            system_classes = participant.get_system_classes()

            participants_data.append({
                'id': participant.id,
                'name': participant.name,
                'inn': participant.inn,
                'industries': participant.industries if participant.industries else [],
                'is_partner': participant.is_partner,
                'system_classes': system_classes,
                'client_count': getattr(participant, 'client_count', 0),
                'system_types_count': getattr(participant, 'system_types_count', 0),
                'registration_date': participant.registration_date,
            })

        total_counts[p_type] = len(participants_data)

        participants_by_type[p_type] = {
            'label': p_label,
            'participants': participants_data,
            'count': len(participants_data),
        }

    context = {
        'participants_by_type': participants_by_type,
        'page_title': 'Участники по типам',
        'total_vendors': total_counts['VENDOR'],
        'total_engineering': total_counts['ENGINEERING'],
        'total_full_cycle': total_counts['FULL_CYCLE'],
        'total_suppliers': total_counts['SUPPLIER'],
    }

    return render(request, 'participants_by_type.html', context)


@login_required
@viewer_required
def automation_report_view(request):
    """Отчёт по автоматизации с фильтрацией и визуализацией"""
    period = request.GET.get('period', 'all')
    detail_level = request.GET.get('detail', 'detailed')
    object_type_filter = request.GET.get('object_type', 'all')

    objects_qs = Object.objects.all()
    if object_type_filter != 'all':
        objects_qs = objects_qs.filter(hierarchy_level=object_type_filter)

    total_objects = objects_qs.count()

    chart_labels = []
    chart_data = []
    distribution_labels = []
    distribution_data = []
    chart_colors = ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40']

    automation_stats = []
    try:
        levels = AutomationLevel.objects.all().order_by('order')

        for level in levels:
            completed_objects = ObjectAutomationLevel.objects.filter(
                level=level,
                status='COMPLETED',
                object__in=objects_qs
            ).values('object').distinct().count()

            all_objects_with_level = ObjectAutomationLevel.objects.filter(
                level=level,
                object__in=objects_qs
            ).values('object').distinct().count()

            percentage = (completed_objects / total_objects * 100) if total_objects > 0 else 0

            if percentage >= 80:
                status_class = 'success'
                status_text = 'Отлично'
            elif percentage >= 50:
                status_class = 'warning'
                status_text = 'Удовлетворительно'
            else:
                status_class = 'danger'
                status_text = 'Требует внимания'

            automation_stats.append({
                'level': level,
                'object_count': completed_objects,
                'all_objects_count': all_objects_with_level,
                'percentage': percentage,
                'status_class': status_class,
                'status_text': status_text
            })

            chart_labels.append(f"{level.code}")
            chart_data.append(round(percentage, 1))

            if all_objects_with_level > 0:
                distribution_labels.append(f"{level.code} ({level.name[:15]})")
                distribution_data.append(all_objects_with_level)

    except Exception as e:
        print(f"Ошибка в статистике автоматизации: {e}")
        automation_stats = []

    class_compliance = []
    compliance_chart_labels = []
    compliance_chart_data = []

    try:
        object_classes = ObjectClass.objects.annotate(
            obj_count=Count('objects_in_class')
        ).filter(obj_count__gt=0).prefetch_related(
            'automation_requirements',
            'objects_in_class'
        )

        for class_obj in object_classes:
            objects_in_class = class_obj.obj_count
            requirements = class_obj.automation_requirements.filter(
                is_mandatory=True
            ).select_related('level')

            if requirements.exists() and objects_in_class > 0:
                compliance_count = 0
                objects_in_class_list = list(class_obj.objects_in_class.all())

                for obj in objects_in_class_list:
                    has_all_levels = True
                    for req in requirements:
                        if not ObjectAutomationLevel.objects.filter(
                            object=obj,
                            level=req.level,
                            status='COMPLETED'
                        ).exists():
                            has_all_levels = False
                            break

                    if has_all_levels:
                        compliance_count += 1

                compliance_percentage = (
                    compliance_count / objects_in_class * 100
                ) if objects_in_class > 0 else 0

                if compliance_percentage >= 90:
                    status_badge = 'success'
                    status_icon = 'fa-check'
                    status_text = 'Соответствует'
                elif compliance_percentage >= 70:
                    status_badge = 'warning'
                    status_icon = 'fa-exclamation-triangle'
                    status_text = 'Частично'
                else:
                    status_badge = 'danger'
                    status_icon = 'fa-times'
                    status_text = 'Не соответствует'

                class_compliance.append({
                    'class': class_obj,
                    'total_objects': objects_in_class,
                    'compliant_objects': compliance_count,
                    'compliance_percentage': compliance_percentage,
                    'status_badge': status_badge,
                    'status_icon': status_icon,
                    'status_text': status_text
                })

                compliance_chart_labels.append(class_obj.name[:20])
                compliance_chart_data.append(round(compliance_percentage, 1))

    except Exception as e:
        print(f"Ошибка в проверке соответствия: {e}")
        class_compliance = []

    automation_stats.sort(key=lambda x: x['percentage'], reverse=True)
    class_compliance.sort(key=lambda x: x['compliance_percentage'], reverse=True)

    context = {
        'automation_stats': automation_stats,
        'class_compliance': class_compliance,
        'total_objects': total_objects,
        'current_period': period,
        'current_detail': detail_level,
        'current_object_type': object_type_filter,
        'chart_labels': chart_labels,
        'chart_data': chart_data,
        'distribution_labels': distribution_labels,
        'distribution_data': distribution_data,
        'compliance_chart_labels': compliance_chart_labels,
        'compliance_chart_data': compliance_chart_data,
        'chart_colors': chart_colors[:len(chart_labels)],
        'has_chart_data': len(chart_data) > 0,
        'has_distribution_data': len(distribution_data) > 0,
        'has_compliance_data': len(compliance_chart_data) > 0,
    }

    return render(request, 'automation_report.html', context)


# =============================================================================
# ГРАФ
# =============================================================================

def graph_view(request):
    """Визуализация связей - полная версия с иерархией и связями"""
    start_total = time.time()

    cache_key = 'graph_data_full_v2'
    cached_data = cache.get(cache_key)

    if cached_data:
        logger.info("Данные графа получены из кэша")
        return render(request, 'graph.html', cached_data)

    logger.info("Генерация данных графа...")

    objects = Object.objects.select_related('parent').only(
        'id', 'name', 'short_name', 'hierarchy_level', 'parent_id',
        'parent__id', 'parent__name', 'parent__short_name', 'parent__hierarchy_level'
    ).all()

    systems = AutomatedSystem.objects.select_related(
        'vendor', 'integrator', 'object', 'level'
    ).all()
    system_list = list(systems)

    participant_ids = set()
    for s in system_list:
        if s.vendor_id:
            participant_ids.add(s.vendor_id)
        if s.integrator_id:
            participant_ids.add(s.integrator_id)

    all_participants = list(Participant.objects.all()[:20])
    for p in all_participants:
        participant_ids.add(p.id)

    participants = Participant.objects.filter(
        id__in=participant_ids
    ).annotate(
        system_count=Count('automated_systems_vendor', distinct=True)
    )

    nodes, edges, node_counts, hierarchy_edges, vendor_edges, system_object_edges, integrator_edges = _build_graph_data(
        objects, system_list, participants
    )

    participants_without_systems = Participant.objects.annotate(
        sys_count=Count('automated_systems_vendor')
    ).filter(sys_count=0)[:5]

    for p in participants_without_systems:
        node_id = f'part_{p.id}'
        if node_id not in {n['id'] for n in nodes}:
            nodes.append({
                'id': node_id,
                'label': p.name[:10],
                'title': f"{p.name}\nТип: {p.get_participant_type_display()}\n(нет систем)",
                'group': 'supplier',
                'color': '#95A5A6',
                'shape': 'dot',
                'size': 14,
            })

    total_time = time.time() - start_total
    stats = {
        'total_nodes': len(nodes),
        'total_edges': len(edges),
        'total_objects': len(objects),
        'total_participants': len(participants),
        'total_systems': len(system_list),
        'object_count': node_counts['object'],
        'vendor_count': node_counts['vendor'],
        'integrator_count': node_counts['integrator'],
        'system_count': node_counts['system'],
        'supplier_count': node_counts['supplier'],
        'hierarchy_edges': hierarchy_edges,
        'vendor_edges': vendor_edges,
        'system_object_edges': system_object_edges,
        'integrator_edges': integrator_edges,
        'debug_time': f"{total_time * 1000:.0f}ms",
    }

    logger.info(f"Время генерации: {total_time * 1000:.2f}ms")
    logger.info(f"Статистика: {stats}")

    context = {
        'graph_data': {
            'nodes': nodes,
            'edges': edges,
        },
        'statistics': stats,
        'has_data': len(nodes) > 0,
    }

    cache.set(cache_key, context, 3600)

    return render(request, 'graph.html', context)


def _build_graph_data(objects, system_list, participants):
    """Строит данные для графа связей"""
    nodes = []
    edges = []
    added_nodes = set()
    edge_keys = set()

    node_counts = {
        'object': 0, 'vendor': 0, 'integrator': 0, 'system': 0, 'supplier': 0
    }

    hierarchy_edges = 0
    vendor_edges = 0
    system_object_edges = 0
    integrator_edges = 0

    for obj in objects:
        node_id = f'obj_{obj.id}'

        if obj.hierarchy_level == 'LEVEL_1':
            color = '#E74C3C'
            shape = 'box'
            size = 30
            level_name = 'Предприятие'
        elif obj.hierarchy_level == 'LEVEL_2':
            color = '#F39C12'
            shape = 'box'
            size = 25
            level_name = 'Цех/Производство'
        else:
            color = '#3498DB'
            shape = 'box'
            size = 20
            level_name = 'Установка'

        label = obj.short_name or obj.name[:15]

        nodes.append({
            'id': node_id,
            'label': label,
            'title': f"{obj.name}\nУровень: {level_name}\nID: {obj.id}",
            'group': 'object',
            'color': color,
            'shape': shape,
            'size': size,
        })
        added_nodes.add(node_id)
        node_counts['object'] += 1

    for obj in objects:
        if obj.parent_id:
            parent_id = f'obj_{obj.parent_id}'
            child_id = f'obj_{obj.id}'

            edge_key = f'hierarchy_{parent_id}_{child_id}'
            if edge_key not in edge_keys:
                edges.append({
                    'from': parent_id,
                    'to': child_id,
                    'label': 'включает',
                    'color': '#95A5A6',
                    'arrows': 'to',
                    'dashes': False,
                    'width': 1,
                })
                edge_keys.add(edge_key)
                hierarchy_edges += 1

    for p in participants:
        node_id = f'part_{p.id}'

        if p.participant_type in ['VENDOR', 'FULL_CYCLE']:
            color = '#2ECC71'
            group = 'vendor'
            size = 20 + min(p.system_count or 0, 15)
            type_name = 'Вендор'
            node_counts['vendor'] += 1
        elif p.participant_type == 'ENGINEERING':
            color = '#9B59B6'
            group = 'integrator'
            size = 18
            type_name = 'Интегратор'
            node_counts['integrator'] += 1
        else:
            color = '#7F8C8D'
            group = 'supplier'
            size = 16
            type_name = 'Поставщик'
            node_counts['supplier'] += 1

        label = p.name[:12]

        nodes.append({
            'id': node_id,
            'label': label,
            'title': f"{p.name}\nТип: {type_name}\nСистем: {p.system_count or 0}\nИНН: {p.inn}",
            'group': group,
            'color': color,
            'shape': 'dot',
            'size': size,
        })
        added_nodes.add(node_id)

    for s in system_list:
        if not s.object:
            continue

        sys_id = f'sys_{s.id}'
        obj_id = f'obj_{s.object.id}'

        if sys_id not in added_nodes:
            system_class_display = (
                s.get_system_class_display()
                if hasattr(s, 'get_system_class_display')
                else s.system_class or 'Не указан'
            )

            nodes.append({
                'id': sys_id,
                'label': s.name[:12],
                'title': f"{s.name}\nКласс: {system_class_display}\nВерсия: {s.version or '—'}",
                'group': 'system',
                'color': '#F1C40F',
                'shape': 'database',
                'size': 14,
            })
            added_nodes.add(sys_id)
            node_counts['system'] += 1

        if s.vendor_id:
            ven_id = f'part_{s.vendor_id}'
            if ven_id in added_nodes:
                edge_key = f'{ven_id}_{sys_id}'
                if edge_key not in edge_keys:
                    edges.append({
                        'from': ven_id,
                        'to': sys_id,
                        'label': 'поставляет',
                        'color': '#2ECC71',
                        'arrows': 'to',
                        'width': 1.5,
                    })
                    edge_keys.add(edge_key)
                    vendor_edges += 1

        edge_key = f'{sys_id}_{obj_id}'
        if edge_key not in edge_keys:
            edges.append({
                'from': sys_id,
                'to': obj_id,
                'label': 'установлена',
                'color': '#F1C40F',
                'arrows': 'to',
                'width': 1.5,
            })
            edge_keys.add(edge_key)
            system_object_edges += 1

        if s.integrator_id:
            int_id = f'part_{s.integrator_id}'
            if int_id in added_nodes:
                edge_key = f'{int_id}_{sys_id}'
                if edge_key not in edge_keys:
                    edges.append({
                        'from': int_id,
                        'to': sys_id,
                        'label': 'внедряет',
                        'color': '#9B59B6',
                        'arrows': 'to',
                        'dashes': True,
                        'width': 1.2,
                    })
                    edge_keys.add(edge_key)
                    integrator_edges += 1

    return nodes, edges, node_counts, hierarchy_edges, vendor_edges, system_object_edges, integrator_edges


def graph_data_api(request):
    """API для получения данных графа в JSON"""
    cache_key = 'graph_data_api_v1'
    data = cache.get(cache_key)

    if not data:
        # Заглушка - в реальности здесь должна быть логика
        data = {
            'nodes': [],
            'edges': [],
            'stats': {}
        }
        cache.set(cache_key, data, 3600)

    return JsonResponse(data)


def graph_view_simple(request):
    """Упрощенная версия для отладки"""
    return render(request, 'graph.html', {'has_data': True})


# =============================================================================
# ИСТОРИЯ (АУДИТ)
# =============================================================================

@login_required
@viewer_required
def object_history_view(request, pk):
    """Просмотр истории изменений объекта"""
    obj = get_object_or_404(Object, pk=pk)
    history = AuditManager.get_history(obj)

    return render(request, 'audit_history.html', {
        'object': obj,
        'history': history,
        'object_name': obj.name,
        'back_url': reverse('object_detail', args=[obj.id]),
    })


@login_required
@viewer_required
def participant_history_view(request, pk):
    """Просмотр истории изменений участника"""
    obj = get_object_or_404(Participant, pk=pk)
    history = AuditManager.get_history(obj)

    return render(request, 'audit_history.html', {
        'object': obj,
        'history': history,
        'object_name': obj.name,
        'back_url': reverse('participant_detail', args=[obj.id]),
    })


@login_required
@viewer_required
def system_history_view(request, pk):
    """Просмотр истории изменений системы"""
    obj = get_object_or_404(AutomatedSystem, pk=pk)
    history = AuditManager.get_history(obj)

    return render(request, 'audit_history.html', {
        'object': obj,
        'history': history,
        'object_name': obj.name,
        'back_url': reverse('automated_system_detail', args=[obj.id]),
    })


# =============================================================================
# ДОПОЛНИТЕЛЬНЫЕ VIEW
# =============================================================================

@login_required
@viewer_required
def legal_entity_detail_view(request, pk):
    """Детальная информация о юридическом лице"""
    legal_entity = get_object_or_404(LegalEntity, id=pk)

    objects = Object.objects.filter(
        legal_entity=legal_entity
    ).select_related(
        'object_class', 'address', 'parent'
    ).prefetch_related('automated_systems')

    context = {
        'legal_entity': legal_entity,
        'objects': objects,
        'total_objects': objects.count(),
    }

    return render(request, 'legal_entity_detail.html', context)


@login_required
@viewer_required
def level_detail_view(request, level_code):
    """Детали по уровням автоматизации"""
    level = get_object_or_404(AutomationLevel, code=level_code)

    objects_with_level = Object.objects.filter(
        automation_levels__level=level,
        automation_levels__status='COMPLETED'
    ).select_related('object_class', 'legal_entity')

    participants = Participant.objects.filter(
        automated_systems_vendor__level=level
    ).distinct()

    class_stats = []
    for class_obj in ObjectClass.objects.all()[:10]:
        count = objects_with_level.filter(object_class=class_obj).count()
        if count > 0:
            class_stats.append({
                'class': class_obj,
                'count': count,
            })

    context = {
        'level': level,
        'objects': objects_with_level,
        'participants': participants,
        'class_stats': class_stats,
        'total_objects': objects_with_level.count(),
    }

    return render(request, 'level_detail.html', context)


def api_objects_by_level(request, level_code):
    """API для получения объектов по уровню (для AJAX)"""
    objects = Object.objects.filter(hierarchy_level=level_code).values(
        'id', 'name', 'category', 'technology'
    )[:50]

    return JsonResponse({'objects': list(objects)})


@login_required
@viewer_required
def db_stats(request):
    """Статистика по базе данных"""
    stats_data = {
        'objects': Object.objects.count(),
        'participants': Participant.objects.count(),
        'systems': AutomatedSystem.objects.count(),
        'by_level': list(Object.objects.values('hierarchy_level').annotate(
            count=Count('id')
        )),
    }

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT schemaname, tablename, tableowner
            FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY tablename;
        """)
        stats_data['tables'] = cursor.fetchall()

    return render(request, 'db_stats.html', {'stats': stats_data})


def fuzzy_search_postgres(search_term, threshold=0.3):
    """
    Нечеткий поиск с использованием PostgreSQL триграмм
    """
    if not search_term or len(search_term) < 2:
        return []

    search_term = search_term.lower().strip()
    original_term = search_term

    corrections = {
        'мзпн': 'мнпз',
        'омзп': 'онпз',
        'нзп': 'нпз',
        'авь': 'авт',
        'г-43-170': 'г-43-107',
        'г43170': 'г-43-107',
        'лч3511': 'лч-35-11',
    }

    if search_term in corrections:
        search_term = corrections[search_term]
        logger.info(f"Исправлена опечатка: {original_term} -> {search_term}")

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id, name, short_name, technology,
                   GREATEST(
                       similarity(name, %s),
                       similarity(short_name, %s),
                       similarity(technology, %s),
                       CASE WHEN %s = ANY(%s) THEN 0.9 ELSE 0 END
                   ) as relevance
            FROM core_object
            WHERE 
                name %% %s OR short_name %% %s OR technology %% %s
                OR name ILIKE %s OR short_name ILIKE %s OR technology ILIKE %s
                OR parent_id IN (
                    SELECT id FROM core_object 
                    WHERE name %% %s OR short_name %% %s
                )
            ORDER BY relevance DESC
            LIMIT 50;
        """, [
            search_term, search_term, search_term,
            search_term, [],
            search_term, search_term, search_term,
            f'%{search_term}%', f'%{search_term}%', f'%{search_term}%',
            search_term, search_term
        ])

        results = cursor.fetchall()
        object_ids = [row[0] for row in results]

        return Object.objects.filter(id__in=object_ids).select_related(
            'parent', 'legal_entity'
        )


def precompute_positions(nodes, edges):
    """Рассчитать позиции узлов на сервере для ускорения отрисовки"""
    try:
        import networkx as nx

        G = nx.Graph()
        for node in nodes:
            G.add_node(node['id'])
        for edge in edges:
            G.add_edge(edge['from'], edge['to'])

        if len(nodes) <= 100:
            pos = nx.spring_layout(G, iterations=30, seed=42)
        else:
            pos = nx.kamada_kawai_layout(G)

        for node in nodes:
            if node['id'] in pos:
                x, y = pos[node['id']]
                node['x'] = float(x) * 800
                node['y'] = float(y) * 600

        logger.info(f"Предрасчет позиций для {len(nodes)} узлов выполнен")
    except ImportError:
        logger.warning("NetworkX не установлен, пропускаем предрасчет позиций")
    except Exception as e:
        logger.error(f"Ошибка при предрасчете позиций: {e}")

    return nodes


# =============================================================================
# ОБРАБОТКА ОШИБОК
# =============================================================================

def custom_404(request, exception):
    """Кастомная страница 404"""
    return render(request, '404.html', status=404)


def custom_500(request):
    """Кастомная страница 500"""
    return render(request, '500.html', status=500)


def user_guide_view(request):
    """Страница руководства пользователя"""
    return render(request, 'user_guide.html')

