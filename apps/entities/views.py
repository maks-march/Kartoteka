"""HTML-представления участников рынка."""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ValidationError

from apps.entities.usecases.entity_usecase import EntityUseCase
from apps.entities.models import Entity
from apps.categories.usecases.category_usecase import CategoryUseCase
from apps.objects.models import ObjectSystem
from apps.system.models import AutomationClass
from common.summary import summary_group as _summary_group


# Простые текстовые поля, считываемые из формы напрямую.
_ENTITY_TEXT_FIELDS = (
    "website",
    "kam_name",
    "kam_phone",
    "contact_person",
    "contact_phone",
    "presentation_url",
    "profile",
)


def _parse_list_field(raw):
    """Список из строки, разделённой запятой или точкой с запятой. Пусто -> None."""
    raw = (raw or "").strip()
    if not raw:
        return None
    import re
    parts = [p.strip() for p in re.split(r"[,;]", raw)]
    parts = [p for p in parts if p]
    return parts or None


def _parse_pairs(post, key_field, value_field):
    """Словарь из параллельных массивов ключ/значение. Пусто -> None."""
    keys = post.getlist(key_field)
    values = post.getlist(value_field)
    result = {}
    for key, value in zip(keys, values):
        key = (key or "").strip()
        if not key:
            continue
        result[key] = (value or "").strip()
    return result or None


def _extract_entity_fields(post):
    """Собирает поля участника из POST."""
    data = {field: post.get(field, "") or "" for field in _ENTITY_TEXT_FIELDS}
    data["inn"] = (post.get("inn") or "").strip() or None
    data["entity_type"] = post.get("entity_type") or ""
    data["is_partner"] = post.get("is_partner") == "on"
    data["registration_date"] = post.get("registration_date") or None
    # Отрасли участника не задаются вручную — вычисляются из связей.
    data["contacts"] = _parse_pairs(post, "contact_key", "contact_value")
    data["financial_data"] = _parse_pairs(post, "fin_key", "fin_value")
    return data


def _parse_pairs_fields(post, class_field, industry_field):
    """Пары (system_class_id, industry_id) из параллельных массивов формы.

    Ссылки nullable: пустое значение допустимо (означает «все»). Отбрасываются
    только строки, где ОБА поля пусты (бессмысленная запись).
    """
    classes = post.getlist(class_field)
    industries = post.getlist(industry_field)
    pairs = []
    for class_id, industry_id in zip(classes, industries):
        class_id = (class_id or "").strip()
        industry_id = (industry_id or "").strip()
        if class_id or industry_id:
            pairs.append((class_id, industry_id))
    return pairs


def _parse_competencies(post):
    """Пары компетенций инж. компании / ФПЦ (comp_class / comp_industry)."""
    return _parse_pairs_fields(post, "comp_class", "comp_industry")


def _parse_exclusions(post):
    """Пары исключений системного интегратора (excl_class / excl_industry)."""
    return _parse_pairs_fields(post, "excl_class", "excl_industry")


def _extract_engineering_fields(post):
    """Поля профиля инжиниринговой компании из POST."""
    return {
        "region": (post.get("region") or "").strip(),
        "resident_object_id": post.get("resident_object") or None,
        "product_ids": post.getlist("product_competencies"),
        "competencies": _parse_competencies(post),
    }


def _form_context(**extra):
    """Общий контекст форм: справочники и т.п."""
    from apps.objects.usecases.object_usecase import ObjectUseCase
    from apps.system.usecases.vendor_product_usecase import VendorProductUseCase
    from apps.system.usecases.automation_class_usecase import AutomationClassUseCase
    from apps.objects.models import Object

    # Отрасли — категории 1-го уровня (объекты, для выбора по id).
    industry_categories = list(CategoryUseCase().list(level=1))
    # Справочник отраслей для combobox компетенции: [{id, label}].
    competency_industries_json = [
        {"id": c.pk, "label": c.category_name} for c in industry_categories
    ]
    # Регионы-подсказки — из существующих объектов.
    regions = sorted({
        r for r in Object.objects.exclude(region="").values_list("region", flat=True) if r
    })
    from apps.system.models import VendorProduct

    entity = extra.get("entity")
    # Для блока вендора: сначала продукты этого вендора (own), затем свободные (free).
    own_products = []
    if entity is not None and getattr(entity, "is_vendor_type", False):
        vp = getattr(entity, "vendor_profile", None)
        if vp is not None:
            own_products = list(vp.products.select_related("system_class"))
    free_products = list(
        VendorProduct.objects.filter(vendor__isnull=True).select_related("system_class")
    )

    # --- Компетенция по продуктам (для инж. компании / вендора полного цикла) ---
    # Полный справочник продуктов; для full_cycle_vendor продукты этого вендора
    # выносим отдельной группой сверху и предвыбираем по умолчанию.
    all_products_list = list(VendorProductUseCase().list())
    own_product_ids = {p.pk for p in own_products}
    competency_own_products = [p for p in all_products_list if p.pk in own_product_ids]
    competency_other_products = [p for p in all_products_list if p.pk not in own_product_ids]

    # Id продуктов, уже отмеченных как компетенция (для предвыбора при редактировании).
    product_competency_ids = set()
    if entity is not None:
        if entity.entity_type == "full_cycle_vendor":
            fcp = getattr(entity, "full_cycle_profile", None)
            if fcp is not None:
                product_competency_ids = set(fcp.products.values_list("pk", flat=True))
            eng = getattr(entity, "engineering_profile", None)
            if eng is not None:
                product_competency_ids |= set(
                    eng.product_competencies.values_list("pk", flat=True)
                )
        elif getattr(entity, "is_engineering_type", False):
            eng = getattr(entity, "engineering_profile", None)
            if eng is not None:
                product_competency_ids = set(
                    eng.product_competencies.values_list("pk", flat=True)
                )
    # Вендор полного цикла: продукты этого вендора входят в специализацию
    # по умолчанию (предвыбраны на уровне подсказок интерфейса).
    if entity is not None and entity.entity_type == "full_cycle_vendor":
        product_competency_ids |= own_product_ids

    classes = AutomationClassUseCase().list()
    # Справочник классов для combobox компетенции по функции: [{id, label, desc}]
    competency_classes_json = [
        {
            "id": c.pk,
            "label": "L{0} - {1}".format(c.level, c.system_class),
            "desc": c.description or "",
        }
        for c in classes
    ]
    # Id продуктов, уже поставляемых этим поставщиком (для предвыбора в форме).
    supplier_product_ids = set()
    if entity is not None and getattr(entity, "is_supplier_type", False):
        sp = getattr(entity, "supplier_profile", None)
        if sp is not None:
            supplier_product_ids = set(sp.products.values_list("pk", flat=True))

    # Существующие пары компетенции (для предзаполнения строк в JS).
    competency_pairs_json = []
    if entity is not None and getattr(entity, "is_engineering_type", False):
        prof = getattr(entity, "engineering_profile", None)
        if prof is not None:
            competency_pairs_json = [
                {"class_id": fc.system_class_id, "industry_id": fc.industry_id}
                for fc in prof.function_competencies.all()
            ]
    # Для full_cycle_vendor используем dedicated full_cycle_profile
    if entity is not None and entity.entity_type == "full_cycle_vendor":
        prof = getattr(entity, "full_cycle_profile", None)
        if prof is not None:
            competency_pairs_json = [
                {"class_id": fc.system_class_id, "industry_id": fc.industry_id}
                for fc in prof.function_competencies.all()
            ]

    # Системный интегратор: вендоры-партнёры (VendorProfile) + управляющая компания.
    from apps.entities.models import VendorProfile
    from apps.owners.usecases.owner_entity_usecase import OwnerEntityUseCase
    vendor_profiles = list(
        VendorProfile.objects.select_related("entity").order_by("entity__entity_name")
    )
    owner_entities = OwnerEntityUseCase().list()
    integrator_partner_ids = set()
    integrator_owner_id = None
    exclusion_pairs_json = []
    if entity is not None and getattr(entity, "is_system_integrator_type", False):
        sip = getattr(entity, "system_integrator_profile", None)
        if sip is not None:
            integrator_partner_ids = set(sip.vendor_partners.values_list("pk", flat=True))
            integrator_owner_id = sip.managing_owner_id
            exclusion_pairs_json = [
                {"class_id": fc.system_class_id, "industry_id": fc.industry_id}
                for fc in sip.function_competencies.all()
            ]
    ctx = {
        "entity_type_choices": Entity.ENTITY_TYPE_CHOICES,
        "industry_categories": industry_categories,
        "competency_industries_json": competency_industries_json,
        "region_suggestions": regions,
        "all_objects": ObjectUseCase().list(),
        "all_products": VendorProductUseCase().list(),
        "all_classes": classes,
        "own_products": own_products,
        "free_products": free_products,
        "competency_own_products": competency_own_products,
        "competency_other_products": competency_other_products,
        "product_competency_ids": product_competency_ids,
        "supplier_product_ids": supplier_product_ids,
        "competency_classes_json": competency_classes_json,
        "competency_pairs_json": competency_pairs_json,
        "vendor_profiles": vendor_profiles,
        "owner_entities": owner_entities,
        "integrator_partner_ids": integrator_partner_ids,
        "integrator_owner_id": integrator_owner_id,
        "exclusion_pairs_json": exclusion_pairs_json,
    }
    ctx.update(extra)
    return ctx


@require_http_methods(["GET"])
def entity_list(request):
    """Список участников рынка в табличном представлении."""
    return _entity_list_render(request, "entities/entity_list.html", "table")


@require_http_methods(["GET"])
def entity_cards(request):
    """Список участников рынка в виде карточек."""
    return _entity_list_render(request, "entities/entity_cards.html", "cards")


def _entity_list_render(request, template, view_mode):
    """Общий рендер списка участников для таблицы и карточек (вспомогательная)."""
    search = request.GET.get("search") or None
    ordering = request.GET.getlist("ordering") or None
    usecase = EntityUseCase()
    entities = usecase.list(search=search, ordering=ordering)
    return render(request, template, {
        "entities": entities,
        "ordering": ordering or [],
        "view_mode": view_mode,
    })


def _entity_detail_context(entity):
    """Собирает общий контекст детальной карточки участника (сводка + связи).

    Используется всеми типовыми страницами участника. Возвращает dict с
    ключами entity / implemented_links / vendor_products / supplied_products /
    summary.
    """
    implemented_links = entity.implemented_object_systems.select_related(
        "object", "system", "system__system_class",
        "system__product__vendor__entity",
    )
    # Продукты, где участник выступает вендором
    vendor_products = entity.products.select_related(
        "vendor", "system_class"
    ).prefetch_related("systems__system_class")

    # Поставляемые продукты (участник — поставщик), со счётчиком систем.
    supplier_profile = getattr(entity, "supplier_profile", None)
    if supplier_profile is not None:
        supplied_products = supplier_profile.products.select_related(
            "vendor__entity", "system_class"
        ).prefetch_related("systems")
    else:
        supplied_products = []

    implemented = list(implemented_links)

    # Вендорские системы вендора — системы, построенные на его продуктах.
    product_systems = [s for p in vendor_products for s in p.systems.all()]

    # ---- Сводка связанности (агрегат из таблиц ниже) ----
    implemented_classes = _summary_group(
        (l.system.system_class for l in implemented if l.system and l.system.system_class),
        key=lambda c: c.pk,
    )
    # Классы вендорских продуктов (для вендора / ФПЦ).
    vendor_classes = _summary_group(
        (p.system_class for p in vendor_products if p.system_class),
        key=lambda c: c.pk,
    )
    # Классы поставляемых продуктов (для поставщика / ФПЦ).
    supplied_classes = _summary_group(
        (p.system_class for p in supplied_products if p.system_class),
        key=lambda c: c.pk,
    )
    # Вендоры внедрённых систем (для системного интегратора): чей продукт стоит.
    implemented_vendors = _summary_group(
        (l.system.product.vendor.entity
         for l in implemented
         if l.system and l.system.product and l.system.product.vendor),
        key=lambda e: e.pk,
    )

    # ---- Статусы внедрения систем (счётчики по статусу, цвет из модели) ----
    status_counts = {}
    for link in implemented:
        status_counts[link.status] = status_counts.get(link.status, 0) + 1
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
    # У исполнителя (интегратор / инж.компания / ФПЦ) — по внедрённым
    # системам; у чистого вендора — по его вендорским системам.
    if entity.can_implement:
        coverage_systems = [link.system for link in implemented if link.system]
    elif entity.is_vendor_type:
        coverage_systems = product_systems
    else:
        coverage_systems = [link.system for link in implemented if link.system]
    level_counts = {}
    for sysm in coverage_systems:
        cls = sysm.system_class
        if cls is not None:
            level_counts[cls.level] = level_counts.get(cls.level, 0) + 1
    level_coverage = [
        {"level": lvl, "label": label, "count": level_counts.get(lvl, 0)}
        for lvl, label in AutomationClass.LEVEL_CHOICES
    ]
    has_level_coverage = any(l["count"] for l in level_coverage)

    # Счётчик продуктов участника: вендорские + поставляемые.
    if entity.can_have_products:
        products_count = vendor_products.count() + len(supplied_products)
    else:
        products_count = None

    summary = {
        "implemented_count": len(implemented),
        "products_count": products_count,
        # Вендорские системы вендора (число систем на его продуктах).
        "product_systems_count": len(product_systems),
        "implemented_classes": implemented_classes,
        "vendor_classes": vendor_classes,
        "supplied_classes": supplied_classes,
        "implemented_vendors": implemented_vendors,
        "is_vendor": entity.can_have_products,
        "status_breakdown": status_breakdown,
        "level_coverage": level_coverage,
        "has_level_coverage": has_level_coverage,
        # Флаги типа — какие группы сводки показывать.
        "is_vendor_type": entity.is_vendor_type,
        "is_supplier_type": entity.is_supplier_type,
        "is_integrator": entity.is_system_integrator_type,
        "can_implement": entity.can_implement,
    }
    return {
        "entity": entity,
        "implemented_links": implemented_links,
        "vendor_products": vendor_products,
        "supplied_products": supplied_products,
        "summary": summary,
    }


# Слаг типа (в URL) -> имя маршрута типовой страницы участника.
ENTITY_TYPE_ROUTES = {
    "vendor": "entity-vendor",
    "supplier": "entity-supplier",
    "system_integrator": "entity-system-integrator",
    "engineering_company": "entity-engineering",
    "full_cycle_vendor": "entity-full-cycle",
}
# Слаг типа -> шаблон типовой страницы.
_ENTITY_TYPE_TEMPLATES = {
    "vendor": "entities/detail/vendor.html",
    "supplier": "entities/detail/supplier.html",
    "system_integrator": "entities/detail/system_integrator.html",
    "engineering_company": "entities/detail/engineering_company.html",
    "full_cycle_vendor": "entities/detail/full_cycle_vendor.html",
}


@require_http_methods(["GET"])
def entity_detail(request, pk):
    """Диспетчер: перенаправляет на типовую страницу участника по его типу.

    Общей страницы больше нет — у каждого типа своя (entity/<id>/<тип>/).
    Ссылки {% url 'entity-detail' pk %} продолжают работать через этот редирект.
    """
    entity = EntityUseCase().get(pk)
    route = ENTITY_TYPE_ROUTES.get(entity.entity_type)
    if route is None:
        # Тип не задан — показываем список (нет специализированной страницы).
        return redirect("entity-list")
    return redirect(route, pk=pk)


def _render_entity_type(request, pk, expected_type):
    """Рендерит типовую страницу участника, проверяя соответствие типа.

    Если тип участника не совпадает с URL — редиректим на его правильную
    типовую страницу (диспетчер).
    """
    entity = EntityUseCase().get(pk)
    if entity.entity_type != expected_type:
        return entity_detail(request, pk)
    return render(request, _ENTITY_TYPE_TEMPLATES[expected_type],
                  _entity_detail_context(entity))


@require_http_methods(["GET"])
def entity_vendor(request, pk):
    """Страница вендора."""
    return _render_entity_type(request, pk, "vendor")


@require_http_methods(["GET"])
def entity_supplier(request, pk):
    """Страница поставщика."""
    return _render_entity_type(request, pk, "supplier")


@require_http_methods(["GET"])
def entity_system_integrator(request, pk):
    """Страница системного интегратора."""
    return _render_entity_type(request, pk, "system_integrator")


@require_http_methods(["GET"])
def entity_engineering(request, pk):
    """Страница инжиниринговой компании."""
    return _render_entity_type(request, pk, "engineering_company")


@require_http_methods(["GET"])
def entity_full_cycle(request, pk):
    """Страница вендора полного цикла."""
    return _render_entity_type(request, pk, "full_cycle_vendor")


@require_http_methods(["GET", "POST"])
@login_required
def entity_create(request):
    """Создание участника: GET — форма, POST — сохранение."""
    error = None
    if request.method == "POST":
        usecase = EntityUseCase()
        try:
            entity = usecase.create(
                entity_name=request.POST.get("entity_name"),
                **_extract_entity_fields(request.POST),
            )
            usecase.save_engineering_profile(entity, **_extract_engineering_fields(request.POST))
            usecase.save_vendor_products(entity, product_ids=request.POST.getlist("vendor_products"))
            usecase.save_supplier_products(entity, product_ids=request.POST.getlist("supplier_products"))
            usecase.save_system_integrator_profile(
                entity,
                managing_owner_id=request.POST.get("managing_owner") or None,
                vendor_partner_ids=request.POST.getlist("vendor_partners"),
                exclusions=_parse_exclusions(request.POST),
            )
            usecase.save_full_cycle_profile(entity, **_extract_engineering_fields(request.POST))
            return redirect("entity-detail", pk=entity.pk)
        except (ValidationError, Exception) as e:
            error = str(e)
    return render(request, "entities/entity_form.html", _form_context(error=error))


@require_http_methods(["GET", "POST"])
@login_required
def entity_edit(request, pk):
    """Редактирование участника: GET — форма, POST — обновление."""
    usecase = EntityUseCase()
    entity = usecase.get(pk)
    error = None

    if request.method == "POST":
        try:
            entity = usecase.update(
                pk=pk,
                entity_name=request.POST.get("entity_name"),
                **_extract_entity_fields(request.POST),
            )
            usecase.save_engineering_profile(entity, **_extract_engineering_fields(request.POST))
            usecase.save_vendor_products(entity, product_ids=request.POST.getlist("vendor_products"))
            usecase.save_supplier_products(entity, product_ids=request.POST.getlist("supplier_products"))
            usecase.save_system_integrator_profile(
                entity,
                managing_owner_id=request.POST.get("managing_owner") or None,
                vendor_partner_ids=request.POST.getlist("vendor_partners"),
                exclusions=_parse_exclusions(request.POST),
            )
            usecase.save_full_cycle_profile(entity, **_extract_engineering_fields(request.POST))
            return redirect("entity-detail", pk=pk)
        except (ValidationError, Exception) as e:
            error = str(e)

    return render(request, "entities/entity_form.html", _form_context(entity=entity, error=error))


@require_http_methods(["POST"])
@login_required
def entity_delete(request, pk):
    """Удаление участника и возврат к списку."""
    usecase = EntityUseCase()
    usecase.delete(pk)
    return redirect("entity-list")
