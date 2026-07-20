"""HTML-представления объектов производства (списки, карточки, формы, детали)."""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ValidationError

from apps.objects.usecases.object_usecase import ObjectUseCase
from apps.objects.usecases.object_system_usecase import ObjectSystemUseCase
from apps.objects.repositories.object_repository import ObjectRepository
from apps.categories.usecases.category_usecase import CategoryUseCase
from apps.system.usecases.system_usecase import SystemUseCase
from apps.owners.usecases.owner_entity_usecase import OwnerEntityUseCase
from apps.entities.usecases.entity_usecase import EntityUseCase
from apps.entities.models import Entity
from apps.objects.models import Object, ObjectSystem
from apps.system.models import AutomationClass
from common.summary import summary_group as _summary_group


# Текстовые/прочие поля объекта, считываемые из формы напрямую.
_OBJECT_TEXT_FIELDS = (
    "object_short_name",
    "object_old_name",
    "object_law_name",
    "object_class",
    "capacity",
    "notes",
    # адресные поля
    "country",
    "region",
    "city",
    "street",
    "house",
    "title",
)


def _extract_object_fields(post, level):
    """Собирает дополнительные поля объекта из POST (вспомогательная).

    title принимаем только для уровней 2 и 3 (на остальных поле в форме скрыто,
    на бэкенде дополнительно валидируется). Поля status/is_reconstructed/
    start_date приводятся к нужным типам.
    """
    data = {}
    for field in _OBJECT_TEXT_FIELDS:
        if field == "title" and level not in (2, 3):
            # Титульный номер применим только к уровням 2 и 3.
            continue
        data[field] = post.get(field, "") or ""

    data["status"] = post.get("status") or "active"
    data["is_reconstructed"] = post.get("is_reconstructed") in ("on", "true", "1", "yes")
    data["start_date"] = post.get("start_date") or None
    return data


# Адресные поля, наследуемые от родителя (синхронно с ObjectUseCase).
_INHERITED_ADDRESS_FIELDS = ("country", "region", "city", "street", "house")


_EMPTY_ADDRESS_DEFAULTS = {f: "" for f in ("country", "region", "city", "street", "house")}


def _parent_address_map(parents):
    """JSON-строка {parent_id: {адресные поля}} для авто-подстановки в форме на клиенте."""
    import json

    mapping = {
        str(p.pk): {field: getattr(p, field, "") or "" for field in _INHERITED_ADDRESS_FIELDS}
        for p in parents
    }
    return json.dumps(mapping, ensure_ascii=False)


@require_http_methods(["GET"])
def object_list(request):
    """Список объектов в табличном представлении."""
    return _object_list_render(request, "objects/object_list.html", "table")


@require_http_methods(["GET"])
def object_cards(request):
    """Список объектов в виде карточек."""
    return _object_list_render(request, "objects/object_cards.html", "cards")


def _object_list_render(request, template, view_mode):
    """Общий рендер списка объектов для таблицы и карточек (вспомогательная).

    Считывает фильтры/сортировку из GET и передаёт в шаблон объекты и
    справочники для фильтров. view_mode различает представления.
    """
    level = request.GET.get("level") or None
    search = request.GET.get("search") or None
    category = request.GET.getlist("category") or None
    system = request.GET.getlist("system") or None
    owner_entity = request.GET.getlist("owner_entity") or None
    ordering = request.GET.getlist("ordering") or None
    usecase = ObjectUseCase()
    cat_usecase = CategoryUseCase()
    system_usecase = SystemUseCase()
    owner_usecase = OwnerEntityUseCase()
    objects = usecase.list(
        level=level,
        search=search,
        category=category,
        system=system,
        owner_entity=owner_entity,
        ordering=ordering,
    )
    all_categories = cat_usecase.list()
    all_systems = system_usecase.list()
    # Фильтр объектов ведём по материнским компаниям (иерархический фильтр
    # сам подтянет объекты дочерних управляющих компаний).
    all_owner_entities = owner_usecase.list_roots()
    return render(request, template, {
        "objects": objects,
        "all_categories": all_categories,
        "all_systems": all_systems,
        "all_owner_entities": all_owner_entities,
        "selected_categories": category or [],
        "selected_systems": system or [],
        "selected_owner_entities": owner_entity or [],
        "ordering": ordering or [],
        "view_mode": view_mode,
    })


@require_http_methods(["GET"])
def object_detail(request, pk):
    """Подробная карточка объекта со сводкой связанности.

    Сводка агрегирует подключённые системы: классы, вендоров, исполнителей,
    разбивку по статусам внедрения и покрытие по уровням автоматизации.
    """
    usecase = ObjectUseCase()
    os_usecase = ObjectSystemUseCase()
    obj = usecase.get(pk)
    children = obj.children.select_related("category").all()
    object_systems = os_usecase.list_for_object(obj)

    # ---- Сводка связанности (агрегат из таблиц ниже) ----
    # Категории дочерних объектов (уникальные, с обрезкой до лимита).
    children_categories = _summary_group(
        (c.category for c in children if c.category),
        key=lambda cat: cat.pk,
    )
    system_classes = _summary_group(
        (os.system.system_class for os in object_systems if os.system and os.system.system_class),
        key=lambda c: c.pk,
    )
    vendors = _summary_group(
        (os.system.product.vendor.entity for os in object_systems
         if os.system and os.system.product and os.system.product.vendor),
        key=lambda e: e.pk,
    )
    implementors = _summary_group(
        (os.implementor for os in object_systems if os.implementor), key=lambda e: e.pk
    )

    # ---- Разбивка систем по статусу внедрения (счётчики по категориям) ----
    # Цвета тегов берём из модели (единая точка правды со статусом в таблице).
    status_counts = {}
    for os in object_systems:
        status_counts[os.status] = status_counts.get(os.status, 0) + 1
    status_breakdown = [
        {
            "label": label,
            "count": status_counts.get(code, 0),
            "tag": ObjectSystem.STATUS_TAG_CLASSES.get(code, "tag-muted"),
        }
        for code, label in ObjectSystem.STATUS_CHOICES
        if status_counts.get(code, 0) > 0
    ]

    # ---- Покрытие по уровням автоматизации L0..L4 (счётчики) ----
    level_counts = {}
    for os in object_systems:
        cls = os.system.system_class if os.system else None
        if cls is not None:
            level_counts[cls.level] = level_counts.get(cls.level, 0) + 1
    level_coverage = [
        {"level": lvl, "label": label, "count": level_counts.get(lvl, 0)}
        for lvl, label in AutomationClass.LEVEL_CHOICES
    ]

    summary = {
        "systems_count": len(object_systems),
        "children_count": children.count(),
        "children_categories": children_categories,
        "system_classes": system_classes,
        "vendors": vendors,
        "implementors": implementors,
        "status_breakdown": status_breakdown,
        "level_coverage": level_coverage,
    }
    return render(request, "objects/object_detail.html", {
        "object": obj,
        "children": children,
        "object_systems": object_systems,
        "summary": summary,
    })


@require_http_methods(["GET", "POST"])
@login_required
def object_create(request):
    """Создание объекта: GET — форма, POST — сохранение через use case."""
    repo = ObjectRepository()
    cat_usecase = CategoryUseCase()
    owner_usecase = OwnerEntityUseCase()
    error = None
    object_instance = None

    if request.method == "POST":
        usecase = ObjectUseCase()
        try:
            level = int(request.POST.get("hierarchy_level"))
            usecase.create(
                user=request.user,
                object_name=request.POST.get("object_name"),
                hierarchy_level=level,
                parent=request.POST.get("parent") or None,
                category=request.POST.get("category") or None,
                owner_entity=request.POST.get("owner_entity") or None,
                **_extract_object_fields(request.POST, level),
            )
            return redirect("object-list")
        except (ValidationError, Exception) as e:
            error = str(e)
            object_instance = None

    possible_parents = repo.get_all().filter(hierarchy_level__lt=3)
    categories = cat_usecase.list()
    owner_entities = owner_usecase.list()
    return render(request, "objects/object_form.html", {
        "object": object_instance,
        "possible_parents": possible_parents,
        "categories": categories,
        "owner_entities": owner_entities,
        "status_choices": Object.STATUS_CHOICES,
        "parent_addresses": _parent_address_map(possible_parents),
        "address_defaults": _EMPTY_ADDRESS_DEFAULTS,
        "error": error,
    })


@require_http_methods(["GET", "POST"])
@login_required
def object_edit(request, pk):
    """Редактирование объекта: GET — форма с данными, POST — обновление."""
    repo = ObjectRepository()
    usecase = ObjectUseCase()
    cat_usecase = CategoryUseCase()
    owner_usecase = OwnerEntityUseCase()
    obj = usecase.get(pk)
    error = None

    if request.method == "POST":
        try:
            level = int(request.POST.get("hierarchy_level"))
            usecase.update(
                pk=pk,
                user=request.user,
                object_name=request.POST.get("object_name"),
                hierarchy_level=level,
                parent=request.POST.get("parent") or None,
                category=request.POST.get("category") or None,
                owner_entity=request.POST.get("owner_entity") or None,
                **_extract_object_fields(request.POST, level),
            )
            return redirect("object-detail", pk=pk)
        except (ValidationError, Exception) as e:
            error = str(e)

    possible_parents = repo.get_all().exclude(pk=pk).filter(hierarchy_level__lt=3)
    categories = cat_usecase.list()
    owner_entities = owner_usecase.list()
    return render(request, "objects/object_form.html", {
        "object": obj,
        "possible_parents": possible_parents,
        "categories": categories,
        "owner_entities": owner_entities,
        "status_choices": Object.STATUS_CHOICES,
        "parent_addresses": _parent_address_map(possible_parents),
        "address_defaults": _EMPTY_ADDRESS_DEFAULTS,
        "error": error,
    })


@require_http_methods(["POST"])
@login_required
def object_delete(request, pk):
    """Удаление объекта и возврат к списку."""
    usecase = ObjectUseCase()
    usecase.delete(pk, request.user)
    return redirect("object-list")


@require_http_methods(["GET", "POST"])
@login_required
def object_add_child(request, pk):
    """Добавление дочернего объекта: привязка существующего или создание нового.

    Список доступных детей ограничен объектами уровнем ниже родителя и очищен
    от кандидатов, создающих цикл (сам родитель, его дети и предки).
    """
    repo = ObjectRepository()
    usecase = ObjectUseCase()
    cat_usecase = CategoryUseCase()
    owner_usecase = OwnerEntityUseCase()
    parent = usecase.get(pk)
    error = None
    active_mode = "existing"

    if parent.hierarchy_level >= 3:
        return redirect("object-detail", pk=pk)

    if request.method == "POST":
        active_mode = request.POST.get("mode") or "existing"
        try:
            if active_mode == "existing":
                child_pk = request.POST.get("existing_object")
                if not child_pk:
                    raise ValidationError("Необходимо выбрать объект")
                usecase.update(pk=int(child_pk), user=request.user, parent=parent.pk)
            else:
                level = int(request.POST.get("hierarchy_level"))
                usecase.create(
                    user=request.user,
                    object_name=request.POST.get("object_name"),
                    hierarchy_level=level,
                    parent=parent.pk,
                    category=request.POST.get("category") or None,
                    owner_entity=request.POST.get("owner_entity") or None,
                    **_extract_object_fields(request.POST, level),
                )
            return redirect("object-detail", pk=pk)
        except (ValidationError, ValueError, TypeError) as e:
            error = str(e)

    # Объекты, которые можно сделать ребенком: только уровнем ниже родителя,
    # исключая самого родителя, его текущих детей и его предков (защита от цикла)
    ancestor_ids = []
    current = parent
    while current.parent_object_id:
        ancestor_ids.append(current.parent_object_id)
        current = current.parent_object

    possible_children = (
        repo.get_all()
        .filter(hierarchy_level__gt=parent.hierarchy_level)
        .exclude(pk=parent.pk)
        .exclude(parent_object_id=parent.pk)
        .exclude(pk__in=ancestor_ids)
    )

    child_levels = [lvl for lvl in (1, 2, 3) if lvl > parent.hierarchy_level]
    categories = cat_usecase.list()
    owner_entities = owner_usecase.list()
    # Предзаполнение адреса наследуемыми полями родителя (с возможностью правок).
    address_defaults = usecase.get_parent_address_defaults(parent.pk)
    return render(request, "objects/object_add_child_form.html", {
        "parent": parent,
        "possible_children": possible_children,
        "child_levels": child_levels,
        "categories": categories,
        "owner_entities": owner_entities,
        "status_choices": Object.STATUS_CHOICES,
        "address_defaults": address_defaults,
        "active_mode": active_mode,
        "error": error,
    })


def _resolve_supplier_from_post(post, system):
    """Определяет поставщика связи из POST-данных формы.

    Если стоит флаг «Поставляется вендором» — поставщиком становится вендор
    продукта системы (участник vendor/full_cycle_vendor). Иначе берётся
    выбранный из списка supplier. Возвращает id участника или None.
    """
    if post.get("supplied_by_vendor"):
        product = getattr(system, "product", None)
        vendor_profile = getattr(product, "vendor", None) if product else None
        vendor_entity = getattr(vendor_profile, "entity", None) if vendor_profile else None
        return vendor_entity.pk if vendor_entity else None
    return post.get("supplier") or None


@require_http_methods(["GET", "POST"])
@login_required
def object_attach_system(request, pk):
    """Привязка системы к объекту: GET — форма, POST — создание связи."""
    usecase = ObjectUseCase()
    os_usecase = ObjectSystemUseCase()
    system_usecase = SystemUseCase()
    entity_usecase = EntityUseCase()
    obj = usecase.get(pk)
    error = None

    if request.method == "POST":
        try:
            system_obj = system_usecase.get(int(request.POST.get("system")))
            os_usecase.attach(
                object_pk=pk,
                system=system_obj.pk,
                status=request.POST.get("status") or "planned",
                implementation_date=request.POST.get("implementation_date") or None,
                implementor=request.POST.get("implementor") or None,
                supplier=_resolve_supplier_from_post(request.POST, system_obj),
            )
            return redirect("object-detail", pk=pk)
        except (ValidationError, ValueError, TypeError) as e:
            error = str(e)

    attached_ids = os_usecase.list_for_object(obj).values_list("system_id", flat=True)
    systems = system_usecase.list().exclude(pk__in=attached_ids).prefetch_related(
        "product__suppliers__entity"
    )
    # Исполнитель внедрения: только интегратор / инж.компания / ФПЦ.
    entities = entity_usecase.list().filter(entity_type__in=Entity.IMPLEMENTOR_TYPES)
    # Поставщик: только поставщик / вендор полного цикла.
    supplier_entities = entity_usecase.list().filter(entity_type__in=Entity.SUPPLIER_TYPES)
    return render(request, "objects/object_system_form.html", {
        "object": obj,
        "systems": systems,
        "entities": entities,
        "supplier_entities": supplier_entities,
        "status_choices": ObjectSystem.STATUS_CHOICES,
        "error": error,
    })


def _object_system_redirect(link, next_page):
    """Возвращает redirect после операции над связью (вспомогательная).

    next_page задаёт, куда вернуться: на страницу системы или объекта.
    """
    if next_page == "system":
        return redirect("system-detail", pk=link.system_id)
    return redirect("object-detail", pk=link.object_id)


@require_http_methods(["GET", "POST"])
@login_required
def object_system_edit(request, pk):
    """Редактирование связи «система на объекте» с двух сторон (объект/система).

    next_page определяет, какую форму показать и куда вернуться после сохранения.
    """
    os_usecase = ObjectSystemUseCase()
    system_usecase = SystemUseCase()
    object_usecase = ObjectUseCase()
    entity_usecase = EntityUseCase()
    link = os_usecase.get(pk)
    next_page = request.POST.get("next") or request.GET.get("next") or "object"
    error = None

    if request.method == "POST":
        try:
            # Система для флага «Поставляется вендором»: новая (если сменили) или текущая.
            sys_pk = int(request.POST.get("system")) if request.POST.get("system") else link.system_id
            system_obj = system_usecase.get(sys_pk)
            link = os_usecase.update(
                pk=pk,
                object_pk=int(request.POST.get("object")) if request.POST.get("object") else None,
                system_pk=int(request.POST.get("system")) if request.POST.get("system") else None,
                status=request.POST.get("status") or "planned",
                implementation_date=request.POST.get("implementation_date") or None,
                implementor=request.POST.get("implementor") or None,
                supplier=_resolve_supplier_from_post(request.POST, system_obj),
            )
            return _object_system_redirect(link, next_page)
        except (ValidationError, ValueError, TypeError) as e:
            error = str(e)

    # Исполнитель внедрения: только интегратор / инж.компания / ФПЦ.
    entities = entity_usecase.list().filter(entity_type__in=Entity.IMPLEMENTOR_TYPES)
    # Поставщик: только поставщик / вендор полного цикла.
    supplier_entities = entity_usecase.list().filter(entity_type__in=Entity.SUPPLIER_TYPES)

    if next_page == "system":
        # Форма как при создании со стороны системы: выбираем объект.
        # Система фиксирована — поставщики ограничены поставщиками её продукта.
        from apps.system.views import _system_product_suppliers
        attached_ids = os_usecase.list_for_system(link.system).values_list("object_id", flat=True)
        objects = object_usecase.list().exclude(pk__in=attached_ids) | object_usecase.list().filter(pk=link.object_id)
        return render(request, "system/system_object_form.html", {
            "system": link.system,
            "objects": objects.distinct(),
            "entities": entities,
            "supplier_entities": _system_product_suppliers(link.system),
            "status_choices": ObjectSystem.STATUS_CHOICES,
            "link": link,
            "next_page": next_page,
            "error": error,
        })

    # Форма как при создании со стороны объекта: выбираем систему
    attached_ids = os_usecase.list_for_object(link.object).values_list("system_id", flat=True)
    systems = (system_usecase.list().exclude(pk__in=attached_ids) | system_usecase.list().filter(pk=link.system_id)).prefetch_related(
        "product__suppliers__entity"
    )
    return render(request, "objects/object_system_form.html", {
        "object": link.object,
        "systems": systems.distinct(),
        "entities": entities,
        "supplier_entities": supplier_entities,
        "status_choices": ObjectSystem.STATUS_CHOICES,
        "link": link,
        "next_page": next_page,
        "error": error,
    })


@require_http_methods(["POST"])
@login_required
def object_system_delete(request, pk):
    """Отвязка системы от объекта с возвратом на исходную страницу."""
    os_usecase = ObjectSystemUseCase()
    link = os_usecase.get(pk)
    next_page = request.POST.get("next") or "object"
    os_usecase.detach(pk)
    return _object_system_redirect(link, next_page)
