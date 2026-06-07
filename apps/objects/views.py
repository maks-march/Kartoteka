from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ValidationError

from apps.objects.usecases.object_usecase import ObjectUseCase
from apps.objects.repositories.object_repository import ObjectRepository


@require_http_methods(["GET"])
def object_list(request):
    level = request.GET.get("level") or None
    search = request.GET.get("search") or None
    usecase = ObjectUseCase()
    objects = usecase.list(level=level, search=search)
    return render(request, "objects/object_list.html", {"objects": objects})


@require_http_methods(["GET"])
def object_detail(request, pk):
    usecase = ObjectUseCase()
    obj = usecase.get(pk)
    children = obj.children.filter(is_deleted=False)
    return render(request, "objects/object_detail.html", {"object": obj, "children": children})


@require_http_methods(["GET", "POST"])
@login_required
def object_create(request):
    repo = ObjectRepository()
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
            )
            return redirect("object-list")
        except (ValidationError, Exception) as e:
            error = str(e)
            object_instance = None

    possible_parents = repo.get_all().filter(level__lt=3)  # любой кроме 3 может быть родителем? на самом деле родитель должен быть меньше уровня ребенка, но для выбора покажем всех возможных
    return render(request, "objects/object_form.html", {
        "object": object_instance,
        "possible_parents": possible_parents,
        "error": error,
    })


@require_http_methods(["GET", "POST"])
@login_required
def object_edit(request, pk):
    repo = ObjectRepository()
    usecase = ObjectUseCase()
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
            )
            return redirect("object-detail", pk=pk)
        except (ValidationError, Exception) as e:
            error = str(e)

    possible_parents = repo.get_all().exclude(pk=pk).filter(level__lt=3)
    return render(request, "objects/object_form.html", {
        "object": obj,
        "possible_parents": possible_parents,
        "error": error,
    })


@require_http_methods(["POST"])
@login_required
def object_delete(request, pk):
    usecase = ObjectUseCase()
    usecase.delete(pk)
    return redirect("object-list")


@require_http_methods(["GET", "POST"])
@login_required
def object_add_child(request, pk):
    repo = ObjectRepository()
    usecase = ObjectUseCase()
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
            )
            return redirect("object-detail", pk=pk)
        except (ValidationError, Exception) as e:
            error = str(e)

    return render(request, "objects/object_form.html", {
        "object": None,
        "possible_parents": [parent],
        "preset_parent": parent.pk,
        "preset_level": child_level,
        "error": error,
    })
