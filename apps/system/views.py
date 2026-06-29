from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ValidationError

from apps.system.usecases.system_usecase import SystemUseCase
from apps.system.usecases.automation_class_usecase import AutomationClassUseCase
from apps.objects.usecases.object_system_usecase import ObjectSystemUseCase
from apps.objects.usecases.object_usecase import ObjectUseCase
from apps.objects.models import ObjectSystem
from apps.participants.usecases.participant_usecase import ParticipantUseCase
from apps.system.models import AutomatedSystem

import json


# Простые текстовые поля системы, считываемые из формы напрямую.
_SYSTEM_TEXT_FIELDS = (
    "autosystem_short_name",
    "version",
    "article",
    "notes",
)

# JSON-поля: в форме вводятся как текст (JSON); пустое -> None, иначе парсим.
_SYSTEM_JSON_FIELDS = ("technical_specs", "modules", "interfaces")


def _parse_json_field(raw, label):
    raw = (raw or "").strip()
    if not raw:
        return None
    try:
        return json.loads(raw)
    except (ValueError, TypeError):
        raise ValidationError(f"Поле «{label}» должно быть корректным JSON")


def _extract_system_fields(post):
    """Собирает дополнительные поля системы из POST."""
    data = {field: post.get(field, "") or "" for field in _SYSTEM_TEXT_FIELDS}
    data["system_status"] = post.get("system_status") or "active"
    data["product_type"] = post.get("product_type") or "software"
    data["release_year"] = post.get("release_year") or None
    data["end_of_support"] = post.get("end_of_support") or None

    json_labels = {
        "technical_specs": "Технические характеристики",
        "modules": "Модули системы",
        "interfaces": "Интерфейсы системы",
    }
    for field in _SYSTEM_JSON_FIELDS:
        data[field] = _parse_json_field(post.get(field), json_labels[field])
    return data


@require_http_methods(["GET"])
def system_list(request):
    system_class = request.GET.get("system_class") or None
    search = request.GET.get("search") or None
    obj = request.GET.getlist("object") or None
    usecase = SystemUseCase()
    class_usecase = AutomationClassUseCase()
    object_usecase = ObjectUseCase()
    systems = usecase.list(system_class=system_class, search=search, obj=obj)
    classes = class_usecase.list()
    all_objects = object_usecase.list()
    return render(request, "system/system_list.html", {
        "systems": systems,
        "classes": classes,
        "all_objects": all_objects,
        "selected_objects": obj or [],
    })


@require_http_methods(["GET"])
def system_detail(request, pk):
    usecase = SystemUseCase()
    os_usecase = ObjectSystemUseCase()
    obj = usecase.get(pk)
    system_objects = os_usecase.list_for_system(obj)
    return render(request, "system/system_detail.html", {
        "system": obj,
        "system_objects": system_objects,
    })


@require_http_methods(["GET", "POST"])
@login_required
def system_create(request):
    class_usecase = AutomationClassUseCase()
    participant_usecase = ParticipantUseCase()
    error = None

    if request.method == "POST":
        usecase = SystemUseCase()
        try:
            usecase.create(
                user=request.user,
                autosystem_name=request.POST.get("autosystem_name"),
                system_class=int(request.POST.get("system_class")),
                vendor=request.POST.get("vendor") or None,
                **_extract_system_fields(request.POST),
            )
            return redirect("system-list")
        except (ValidationError, Exception) as e:
            error = str(e)

    classes = class_usecase.list()
    participants = participant_usecase.list()
    return render(request, "system/system_form.html", {
        "classes": classes,
        "participants": participants,
        "status_choices": AutomatedSystem.STATUS_CHOICES,
        "product_type_choices": AutomatedSystem.PRODUCT_TYPE_CHOICES,
        "error": error,
    })


@require_http_methods(["GET", "POST"])
@login_required
def system_edit(request, pk):
    usecase = SystemUseCase()
    class_usecase = AutomationClassUseCase()
    participant_usecase = ParticipantUseCase()
    obj = usecase.get(pk)
    error = None

    if request.method == "POST":
        try:
            usecase.update(
                pk=pk,
                user=request.user,
                autosystem_name=request.POST.get("autosystem_name"),
                system_class=int(request.POST.get("system_class")),
                vendor=request.POST.get("vendor") or None,
                **_extract_system_fields(request.POST),
            )
            return redirect("system-detail", pk=pk)
        except (ValidationError, Exception) as e:
            error = str(e)

    classes = class_usecase.list()
    participants = participant_usecase.list()
    return render(request, "system/system_form.html", {
        "system": obj,
        "classes": classes,
        "participants": participants,
        "status_choices": AutomatedSystem.STATUS_CHOICES,
        "product_type_choices": AutomatedSystem.PRODUCT_TYPE_CHOICES,
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
    participant_usecase = ParticipantUseCase()
    system = usecase.get(pk)
    error = None

    if request.method == "POST":
        try:
            os_usecase.attach(
                object_pk=int(request.POST.get("object")),
                system_pk=pk,
                status=request.POST.get("status") or "planned",
                implementation_date=request.POST.get("implementation_date") or None,
                integrator=request.POST.get("integrator") or None,
                implimentor=request.POST.get("implimentor") or None,
            )
            return redirect("system-detail", pk=pk)
        except (ValidationError, ValueError, TypeError) as e:
            error = str(e)

    attached_ids = os_usecase.list_for_system(system).values_list("object_id", flat=True)
    objects = object_usecase.list().exclude(pk__in=attached_ids)
    participants = participant_usecase.list()
    return render(request, "system/system_object_form.html", {
        "system": system,
        "objects": objects,
        "participants": participants,
        "status_choices": ObjectSystem.STATUS_CHOICES,
        "error": error,
    })
