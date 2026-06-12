from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ValidationError

from apps.system.usecases.system_usecase import SystemUseCase
from apps.system.usecases.automation_class_usecase import AutomationClassUseCase


@require_http_methods(["GET"])
def system_list(request):
    system_class = request.GET.get("system_class") or None
    search = request.GET.get("search") or None
    usecase = SystemUseCase()
    class_usecase = AutomationClassUseCase()
    systems = usecase.list(system_class=system_class, search=search)
    classes = class_usecase.list()
    return render(request, "system/system_list.html", {
        "systems": systems,
        "classes": classes,
    })


@require_http_methods(["GET"])
def system_detail(request, pk):
    usecase = SystemUseCase()
    obj = usecase.get(pk)
    return render(request, "system/system_detail.html", {"system": obj})


@require_http_methods(["GET", "POST"])
@login_required
def system_create(request):
    class_usecase = AutomationClassUseCase()
    error = None

    if request.method == "POST":
        usecase = SystemUseCase()
        try:
            usecase.create(
                user=request.user,
                autosystem_name=request.POST.get("autosystem_name"),
                system_class=int(request.POST.get("system_class")),
            )
            return redirect("system-list")
        except (ValidationError, Exception) as e:
            error = str(e)

    classes = class_usecase.list()
    return render(request, "system/system_form.html", {
        "classes": classes,
        "error": error,
    })


@require_http_methods(["GET", "POST"])
@login_required
def system_edit(request, pk):
    usecase = SystemUseCase()
    class_usecase = AutomationClassUseCase()
    obj = usecase.get(pk)
    error = None

    if request.method == "POST":
        try:
            usecase.update(
                pk=pk,
                user=request.user,
                autosystem_name=request.POST.get("autosystem_name"),
                system_class=int(request.POST.get("system_class")),
            )
            return redirect("system-detail", pk=pk)
        except (ValidationError, Exception) as e:
            error = str(e)

    classes = class_usecase.list()
    return render(request, "system/system_form.html", {
        "system": obj,
        "classes": classes,
        "error": error,
    })


@require_http_methods(["POST"])
@login_required
def system_delete(request, pk):
    usecase = SystemUseCase()
    usecase.delete(pk, request.user)
    return redirect("system-list")
