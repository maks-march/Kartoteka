from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ValidationError

from apps.categories.usecases.category_usecase import CategoryUseCase
from apps.objects.usecases.object_usecase import ObjectUseCase


@require_http_methods(["GET"])
def category_list(request):
    level = request.GET.get("level") or None
    search = request.GET.get("search") or None
    usecase = CategoryUseCase()
    categories = usecase.list(level=level, search=search)
    return render(request, "categories/category_list.html", {"categories": categories})


@require_http_methods(["GET"])
def category_detail(request, pk):
    cat_usecase = CategoryUseCase()
    obj_usecase = ObjectUseCase()
    category = cat_usecase.get(pk)
    objects = obj_usecase.list(category=pk)
    return render(request, "categories/category_detail.html", {
        "category": category,
        "objects": objects,
    })


@require_http_methods(["GET", "POST"])
@login_required
def category_create(request):
    error = None
    if request.method == "POST":
        usecase = CategoryUseCase()
        try:
            usecase.create(
                user=request.user,
                name=request.POST.get("name"),
                level=int(request.POST.get("level")),
            )
            return redirect("category-list")
        except (ValidationError, Exception) as e:
            error = str(e)
    return render(request, "categories/category_form.html", {"error": error})


@require_http_methods(["GET", "POST"])
@login_required
def category_edit(request, pk):
    usecase = CategoryUseCase()
    obj = usecase.get(pk)
    error = None

    if request.method == "POST":
        try:
            usecase.update(
                pk=pk,
                user=request.user,
                name=request.POST.get("name"),
                level=int(request.POST.get("level")),
            )
            return redirect("category-list")
        except (ValidationError, Exception) as e:
            error = str(e)

    return render(request, "categories/category_form.html", {"category": obj, "error": error})


@require_http_methods(["POST"])
@login_required
def category_delete(request, pk):
    usecase = CategoryUseCase()
    usecase.delete(pk, request.user)
    return redirect("category-list")
