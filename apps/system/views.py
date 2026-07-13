"""HTML-представления автоматизированных систем (списки, карточки, формы, детали)."""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ValidationError

from apps.system.usecases.system_usecase import SystemUseCase
from apps.system.usecases.automation_class_usecase import AutomationClassUseCase
from apps.system.usecases.vendor_product_usecase import VendorProductUseCase
from apps.objects.usecases.object_system_usecase import ObjectSystemUseCase
from apps.objects.usecases.object_usecase import ObjectUseCase
from apps.objects.models import ObjectSystem
from apps.entities.usecases.entity_usecase import EntityUseCase
from apps.categories.usecases.category_usecase import CategoryUseCase
from apps.system.models import AutomationSystem, VendorProduct
from common.summary import summary_group as _summary_group


# Простые текстовые поля системы, считываемые из формы напрямую.
_SYSTEM_TEXT_FIELDS = (
    "autosystem_short_name",
    "notes",
)


def _parse_list_field(raw):
    """Список из строки, разделённой запятой или точкой с запятой.

    Пустая строка -> None. Пустые элементы отбрасываются, пробелы обрезаются.
    """
    raw = (raw or "").strip()
    if not raw:
        return None
    import re
    parts = [p.strip() for p in re.split(r"[,;]", raw)]
    parts = [p for p in parts if p]
    return parts or None


def _parse_specs_pairs(post):
    """Словарь технических характеристик из параллельных массивов
    spec_key / spec_value. Пустые ключи пропускаются. Пусто -> None."""
    keys = post.getlist("spec_key")
    values = post.getlist("spec_value")
    specs = {}
    for key, value in zip(keys, values):
        key = (key or "").strip()
        if not key:
            continue
        specs[key] = (value or "").strip()
    return specs or None


def _extract_system_fields(post):
    """Собирает дополнительные поля системы из POST."""
    data = {field: post.get(field, "") or "" for field in _SYSTEM_TEXT_FIELDS}
    data["system_status"] = post.get("system_status") or "active"
    data["release_year"] = post.get("release_year") or None

    # Списки — через запятую/точку с запятой; характеристики — пары ключ/значение.
    data["modules"] = _parse_list_field(post.get("modules"))
    data["interfaces"] = _parse_list_field(post.get("interfaces"))
    data["technical_specs"] = _parse_specs_pairs(post)
    return data


@require_http_methods(["GET"])
def system_list(request):
    return _system_list_render(request, "system/system_list.html", "table")


@require_http_methods(["GET"])
def system_cards(request):
    return _system_list_render(request, "system/system_cards.html", "cards")


def _system_list_render(request, template, view_mode):
    system_class = request.GET.get("system_class") or None
    search = request.GET.get("search") or None
    obj = request.GET.getlist("object") or None
    product = request.GET.getlist("product") or None
    system_status = request.GET.getlist("system_status") or None
    ordering = request.GET.getlist("ordering") or None

    usecase = SystemUseCase()
    class_usecase = AutomationClassUseCase()
    object_usecase = ObjectUseCase()
    product_usecase = VendorProductUseCase()

    systems = usecase.list(
        system_class=system_class,
        search=search,
        obj=obj,
        product=product,
        system_status=system_status,
        ordering=ordering,
    )
    classes = class_usecase.list()
    all_objects = object_usecase.list()
    all_products = product_usecase.list()
    return render(request, template, {
        "systems": systems,
        "classes": classes,
        "all_objects": all_objects,
        "all_products": all_products,
        "status_choices": AutomationSystem.STATUS_CHOICES,
        "selected_objects": obj or [],
        "selected_products": product or [],
        "selected_statuses": system_status or [],
        "ordering": ordering or [],
        "view_mode": view_mode,
    })


@require_http_methods(["GET"])
def system_detail(request, pk):
    usecase = SystemUseCase()
    os_usecase = ObjectSystemUseCase()
    obj = usecase.get(pk)
    system_objects = os_usecase.list_for_system(obj)

    # ---- Сводка связанности (агрегат из таблицы «Подключенные объекты») ----
    implementors = _summary_group(
        (os.implementor for os in system_objects if os.implementor), key=lambda e: e.pk
    )
    summary = {
        "objects_count": len(system_objects),
        "implementors": implementors,
    }
    return render(request, "system/system_detail.html", {
        "system": obj,
        "system_objects": system_objects,
        "summary": summary,
    })


@require_http_methods(["GET", "POST"])
@login_required
def system_create(request):
    class_usecase = AutomationClassUseCase()
    product_usecase = VendorProductUseCase()
    error = None

    if request.method == "POST":
        usecase = SystemUseCase()
        try:
            usecase.create(
                user=request.user,
                autosystem_name=request.POST.get("autosystem_name"),
                system_class=int(request.POST.get("system_class")),
                product=request.POST.get("product") or None,
                subsystem_classes=request.POST.getlist("subsystem_classes"),
                **_extract_system_fields(request.POST),
            )
            return redirect("system-list")
        except (ValidationError, Exception) as e:
            error = str(e)

    classes = class_usecase.list()
    products = product_usecase.list()
    return render(request, "system/system_form.html", {
        "classes": classes,
        "products": products,
        "status_choices": AutomationSystem.STATUS_CHOICES,
        "error": error,
    })


@require_http_methods(["GET", "POST"])
@login_required
def system_edit(request, pk):
    usecase = SystemUseCase()
    class_usecase = AutomationClassUseCase()
    product_usecase = VendorProductUseCase()
    obj = usecase.get(pk)
    error = None

    if request.method == "POST":
        try:
            usecase.update(
                pk=pk,
                user=request.user,
                autosystem_name=request.POST.get("autosystem_name"),
                system_class=int(request.POST.get("system_class")),
                product=request.POST.get("product") or None,
                subsystem_classes=request.POST.getlist("subsystem_classes"),
                **_extract_system_fields(request.POST),
            )
            return redirect("system-detail", pk=pk)
        except (ValidationError, Exception) as e:
            error = str(e)

    classes = class_usecase.list()
    products = product_usecase.list()
    return render(request, "system/system_form.html", {
        "system": obj,
        "classes": classes,
        "products": products,
        "selected_subsystem_ids": list(obj.subsystem_classes.values_list("id", flat=True)),
        "status_choices": AutomationSystem.STATUS_CHOICES,
        "error": error,
    })


@require_http_methods(["POST"])
@login_required
def system_delete(request, pk):
    usecase = SystemUseCase()
    usecase.delete(pk, request.user)
    return redirect("system-list")


@require_http_methods(["GET", "POST"])
@login_required
def system_attach_object(request, pk):
    usecase = SystemUseCase()
    os_usecase = ObjectSystemUseCase()
    object_usecase = ObjectUseCase()
    entity_usecase = EntityUseCase()
    system = usecase.get(pk)
    error = None

    if request.method == "POST":
        try:
            os_usecase.attach(
                object_pk=int(request.POST.get("object")),
                system_pk=pk,
                status=request.POST.get("status") or "planned",
                implementation_date=request.POST.get("implementation_date") or None,
                implementor=request.POST.get("implementor") or None,
            )
            return redirect("system-detail", pk=pk)
        except (ValidationError, ValueError, TypeError) as e:
            error = str(e)

    attached_ids = os_usecase.list_for_system(system).values_list("object_id", flat=True)
    objects = object_usecase.list().exclude(pk__in=attached_ids)
    entities = entity_usecase.list()
    return render(request, "system/system_object_form.html", {
        "system": system,
        "objects": objects,
        "entities": entities,
        "status_choices": ObjectSystem.STATUS_CHOICES,
        "error": error,
    })


# ===================== Продукты вендоров =====================

@require_http_methods(["GET"])
def product_list(request):
    search = request.GET.get("search") or None
    system_class = request.GET.get("system_class") or None
    ordering = request.GET.getlist("ordering") or None
    usecase = VendorProductUseCase()
    products = usecase.list(search=search, system_class=system_class, ordering=ordering)
    return render(request, "system/product_list.html", {
        "products": products,
        "classes": AutomationClassUseCase().list(),
        "selected_class": system_class or "",
        "ordering": ordering or [],
    })


@require_http_methods(["GET"])
def product_detail(request, pk):
    usecase = VendorProductUseCase()
    product = usecase.get(pk)
    systems = product.systems.select_related("system_class")
    return render(request, "system/product_detail.html", {
        "product": product,
        "systems": systems,
    })


def _extract_product_fields(post):
    """Дополнительные поля продукта из POST."""
    return {
        "product_type": post.get("product_type") or "",
        "system_class": post.get("system_class") or None,
        "description": post.get("description", "") or "",
        "version": post.get("version", "") or "",
        "release_year": post.get("release_year") or None,
        "end_of_support": post.get("end_of_support") or None,
        "technical_specs": _parse_specs_pairs(post),
        "industries": _parse_list_field(post.get("industries")),
    }


def _product_form_context(**extra):
    # В выборе вендора — только участники типа vendor / full_cycle_vendor
    # (продукт может принадлежать только им).
    vendors = [e for e in EntityUseCase().list() if e.is_vendor_type]
    ctx = {
        "vendors": vendors,
        "classes": AutomationClassUseCase().list(),
        "product_type_choices": VendorProduct.PRODUCT_TYPE_CHOICES,
        # Отрасли-подсказки: категории 1-го уровня (без связи, только значения).
        "industry_suggestions": [c.category_name for c in CategoryUseCase().list(level=1)],
    }
    ctx.update(extra)
    return ctx


@require_http_methods(["GET", "POST"])
@login_required
def product_create(request):
    error = None
    if request.method == "POST":
        usecase = VendorProductUseCase()
        try:
            product = usecase.create(
                product_name=request.POST.get("product_name"),
                vendor=request.POST.get("vendor") or None,
                subsystem_classes=request.POST.getlist("subsystem_classes"),
                **_extract_product_fields(request.POST),
            )
            return redirect("product-detail", pk=product.pk)
        except (ValidationError, Exception) as e:
            error = str(e)
    return render(request, "system/product_form.html", _product_form_context(error=error))


@require_http_methods(["GET", "POST"])
@login_required
def product_edit(request, pk):
    usecase = VendorProductUseCase()
    product = usecase.get(pk)
    error = None

    if request.method == "POST":
        try:
            usecase.update(
                pk=pk,
                product_name=request.POST.get("product_name"),
                vendor=request.POST.get("vendor") or None,
                subsystem_classes=request.POST.getlist("subsystem_classes"),
                **_extract_product_fields(request.POST),
            )
            return redirect("product-detail", pk=pk)
        except (ValidationError, Exception) as e:
            error = str(e)

    return render(request, "system/product_form.html", _product_form_context(
        product=product,
        selected_subsystem_ids=list(product.subsystem_classes.values_list("id", flat=True)),
        error=error,
    ))


@require_http_methods(["POST"])
@login_required
def product_delete(request, pk):
    usecase = VendorProductUseCase()
    usecase.delete(pk)
    return redirect("product-list")
