"""HTML-представления участников рынка."""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ValidationError

from apps.entities.usecases.entity_usecase import EntityUseCase
from apps.entities.models import Entity
from apps.categories.usecases.category_usecase import CategoryUseCase


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
    data["industries"] = _parse_list_field(post.get("industries"))
    data["contacts"] = _parse_pairs(post, "contact_key", "contact_value")
    data["financial_data"] = _parse_pairs(post, "fin_key", "fin_value")
    return data


def _form_context(**extra):
    """Общий контекст форм: справочники и т.п."""
    industries = [c.name for c in CategoryUseCase().list(level=1)]
    ctx = {
        "entity_type_choices": Entity.ENTITY_TYPE_CHOICES,
        "industry_suggestions": industries,
    }
    ctx.update(extra)
    return ctx


@require_http_methods(["GET"])
def entity_list(request):
    return _entity_list_render(request, "entities/entity_list.html", "table")


@require_http_methods(["GET"])
def entity_cards(request):
    return _entity_list_render(request, "entities/entity_cards.html", "cards")


def _entity_list_render(request, template, view_mode):
    search = request.GET.get("search") or None
    ordering = request.GET.getlist("ordering") or None
    usecase = EntityUseCase()
    entities = usecase.list(search=search, ordering=ordering)
    return render(request, template, {
        "entities": entities,
        "ordering": ordering or [],
        "view_mode": view_mode,
    })


@require_http_methods(["GET"])
def entity_detail(request, pk):
    usecase = EntityUseCase()
    entity = usecase.get(pk)
    integrated_links = entity.integrated_object_systems.select_related("object", "system")
    implemented_links = entity.implemented_object_systems.select_related("object", "system")
    # Продукты, где участник выступает вендором
    vendor_products = entity.products.all()
    return render(request, "entities/entity_detail.html", {
        "entity": entity,
        "integrated_links": integrated_links,
        "implemented_links": implemented_links,
        "vendor_products": vendor_products,
    })


@require_http_methods(["GET", "POST"])
@login_required
def entity_create(request):
    error = None
    if request.method == "POST":
        usecase = EntityUseCase()
        try:
            entity = usecase.create(
                entity_name=request.POST.get("entity_name"),
                **_extract_entity_fields(request.POST),
            )
            return redirect("entity-detail", pk=entity.pk)
        except (ValidationError, Exception) as e:
            error = str(e)
    return render(request, "entities/entity_form.html", _form_context(error=error))


@require_http_methods(["GET", "POST"])
@login_required
def entity_edit(request, pk):
    usecase = EntityUseCase()
    entity = usecase.get(pk)
    error = None

    if request.method == "POST":
        try:
            usecase.update(
                pk=pk,
                entity_name=request.POST.get("entity_name"),
                **_extract_entity_fields(request.POST),
            )
            return redirect("entity-detail", pk=pk)
        except (ValidationError, Exception) as e:
            error = str(e)

    return render(request, "entities/entity_form.html", _form_context(entity=entity, error=error))


@require_http_methods(["POST"])
@login_required
def entity_delete(request, pk):
    usecase = EntityUseCase()
    usecase.delete(pk)
    return redirect("entity-list")
