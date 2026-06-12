from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ValidationError

from apps.objects.usecases.object_usecase import ObjectUseCase
from apps.objects.usecases.object_system_usecase import ObjectSystemUseCase
from apps.objects.repositories.object_repository import ObjectRepository
from apps.categories.usecases.category_usecase import CategoryUseCase
from apps.system.usecases.system_usecase import SystemUseCase
from apps.objects.models import ObjectSystem


@require_http_methods(["GET"])
def object_list(request):
    level = request.GET.get("level") or None
    search = request.GET.get("search") or None
    category = request.GET.get("category") or None
    usecase = ObjectUseCase()
    cat_usecase = CategoryUseCase()
    objects = usecase.list(level=level, search=search, category=category)
    all_categories = cat_usecase.list()
    return render(request, "objects/object_list.html", {"objects": objects, "all_categories": all_categories})


@require_http_methods(["GET"])
def object_detail(request, pk):
    usecase = ObjectUseCase()
    os_usecase = ObjectSystemUseCase()
    obj = usecase.get(pk)
    children = obj.children.filter(is_deleted=False)
    object_systems = os_usecase.list_for_object(obj)
    return render(request, "objects/object_detail.html", {
        "object": obj,
        "children": children,
        "object_systems": object_systems,
    })


@require_http_methods(["GET", "POST"])
@login_required
def object_create(request):
    repo = ObjectRepository()
    cat_usecase = CategoryUseCase()
    error = None
    object_instance = None

    if request.method == "POST":
        usecase = ObjectUseCase()
        try:
            usecase.create(
                user=request.user,
                name=request.POST.get("name"),
                level=int(request.POST.get("level")),
                parent=request.POST.get("parent") or None,
                category=request.POST.get("category") or None,
            )
            return redirect("object-list")
        except (ValidationError, Exception) as e:
            error = str(e)
            object_instance = None

    possible_parents = repo.get_all().filter(level__lt=3)
    categories = cat_usecase.list()
    return render(request, "objects/object_form.html", {
        "object": object_instance,
        "possible_parents": possible_parents,
        "categories": categories,
        "error": error,
    })


@require_http_methods(["GET", "POST"])
@login_required
def object_edit(request, pk):
    repo = ObjectRepository()
    usecase = ObjectUseCase()
    cat_usecase = CategoryUseCase()
    obj = usecase.get(pk)
    error = None

    if request.method == "POST":
        try:
            usecase.update(
                pk=pk,
                user=request.user,
                name=request.POST.get("name"),
                level=int(request.POST.get("level")),
                parent=request.POST.get("parent") or None,
                category=request.POST.get("category") or None,
            )
            return redirect("object-detail", pk=pk)
        except (ValidationError, Exception) as e:
            error = str(e)

    possible_parents = repo.get_all().exclude(pk=pk).filter(level__lt=3)
    categories = cat_usecase.list()
    return render(request, "objects/object_form.html", {
        "object": obj,
        "possible_parents": possible_parents,
        "categories": categories,
        "error": error,
    })


@require_http_methods(["POST"])
@login_required
def object_delete(request, pk):
    usecase = ObjectUseCase()
    usecase.delete(pk, request.user)
    return redirect("object-list")


@require_http_methods(["GET", "POST"])
@login_required
def object_add_child(request, pk):
    repo = ObjectRepository()
    usecase = ObjectUseCase()
    cat_usecase = CategoryUseCase()
    parent = usecase.get(pk)
    error = None

    if parent.level >= 3:
        return redirect("object-detail", pk=pk)

    child_level = parent.level + 1

    if request.method == "POST":
        try:
            usecase.create(
                user=request.user,
                name=request.POST.get("name"),
                level=child_level,
                parent=parent.pk,
                category=request.POST.get("category") or None,
            )
            return redirect("object-detail", pk=pk)
        except (ValidationError, Exception) as e:
            error = str(e)

    categories = cat_usecase.list(level=child_level)
    return render(request, "objects/object_form.html", {
        "object": None,
        "possible_parents": [parent],
        "categories": categories,
        "preset_parent": parent.pk,
        "preset_level": child_level,
        "error": error,
    })


@require_http_methods(["GET", "POST"])
@login_required
def object_attach_system(request, pk):
    usecase = ObjectUseCase()
    os_usecase = ObjectSystemUseCase()
    system_usecase = SystemUseCase()
    obj = usecase.get(pk)
    error = None

    if request.method == "POST":
        try:
            os_usecase.attach(
                object_pk=pk,
                system=int(request.POST.get("system")),
                status=request.POST.get("status") or "planned",
                implementation_date=request.POST.get("implementation_date") or None,
            )
            return redirect("object-detail", pk=pk)
        except (ValidationError, ValueError, TypeError) as e:
            error = str(e)

    attached_ids = os_usecase.list_for_object(obj).values_list("system_id", flat=True)
    systems = system_usecase.list().exclude(pk__in=attached_ids)
    return render(request, "objects/object_system_form.html", {
        "object": obj,
        "systems": systems,
        "status_choices": ObjectSystem.STATUS_CHOICES,
        "error": error,
    })


def _object_system_redirect(link, next_page):
    if next_page == "system":
        return redirect("system-detail", pk=link.system_id)
    return redirect("object-detail", pk=link.object_id)


@require_http_methods(["GET", "POST"])
@login_required
def object_system_edit(request, pk):
    os_usecase = ObjectSystemUseCase()
    system_usecase = SystemUseCase()
    object_usecase = ObjectUseCase()
    link = os_usecase.get(pk)
    next_page = request.POST.get("next") or request.GET.get("next") or "object"
    error = None

    if request.method == "POST":
        try:
            link = os_usecase.update(
                pk=pk,
                object_pk=int(request.POST.get("object")) if request.POST.get("object") else None,
                system_pk=int(request.POST.get("system")) if request.POST.get("system") else None,
                status=request.POST.get("status") or "planned",
                implementation_date=request.POST.get("implementation_date") or None,
            )
            return _object_system_redirect(link, next_page)
        except (ValidationError, ValueError, TypeError) as e:
            error = str(e)

    if next_page == "system":
        # Форма как при создании со стороны системы: выбираем объект
        attached_ids = os_usecase.list_for_system(link.system).values_list("object_id", flat=True)
        objects = object_usecase.list().exclude(pk__in=attached_ids) | object_usecase.list().filter(pk=link.object_id)
        return render(request, "system/system_object_form.html", {
            "system": link.system,
            "objects": objects.distinct(),
            "status_choices": ObjectSystem.STATUS_CHOICES,
            "link": link,
            "next_page": next_page,
            "error": error,
        })

    # Форма как при создании со стороны объекта: выбираем систему
    attached_ids = os_usecase.list_for_object(link.object).values_list("system_id", flat=True)
    systems = system_usecase.list().exclude(pk__in=attached_ids) | system_usecase.list().filter(pk=link.system_id)
    return render(request, "objects/object_system_form.html", {
        "object": link.object,
        "systems": systems.distinct(),
        "status_choices": ObjectSystem.STATUS_CHOICES,
        "link": link,
        "next_page": next_page,
        "error": error,
    })


@require_http_methods(["POST"])
@login_required
def object_system_delete(request, pk):
    os_usecase = ObjectSystemUseCase()
    link = os_usecase.get(pk)
    next_page = request.POST.get("next") or "object"
    os_usecase.detach(pk)
    return _object_system_redirect(link, next_page)
