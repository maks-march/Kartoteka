from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ValidationError

from apps.owners.usecases.owner_entity_usecase import OwnerEntityUseCase


@require_http_methods(["GET"])
def owner_entity_list(request):
    search = request.GET.get("search") or None
    usecase = OwnerEntityUseCase()
    owner_entities = usecase.list(search=search)
    return render(request, "owners/owner_entity_list.html", {
        "owner_entities": owner_entities,
    })


@require_http_methods(["GET"])
def owner_entity_detail(request, pk):
    usecase = OwnerEntityUseCase()
    owner_entity = usecase.get(pk)
    child_entities = owner_entity.subsidiaries.all().order_by("owner_name")
    objects = owner_entity.owned_objects.filter(is_deleted=False).select_related("category", "parent")
    return render(request, "owners/owner_entity_detail.html", {
        "owner_entity": owner_entity,
        "child_entities": child_entities,
        "objects": objects,
    })


@require_http_methods(["GET", "POST"])
@login_required
def owner_entity_create(request):
    usecase = OwnerEntityUseCase()
    error = None

    if request.method == "POST":
        try:
            data = {
                "owner_name": request.POST.get("owner_name"),
                "owner": request.POST.get("owner") or None,
            }
            if request.POST.get("ultimate_owner"):
                data["ultimate_owner"] = request.POST.get("ultimate_owner")
            owner_entity = usecase.create(**data)
            return redirect("owner-entity-detail", pk=owner_entity.pk)
        except (ValidationError, Exception) as e:
            error = str(e)

    possible_owners = usecase.list()
    return render(request, "owners/owner_entity_form.html", {
        "possible_owners": possible_owners,
        "possible_ultimate_owners": possible_owners,
        "error": error,
    })


@require_http_methods(["GET", "POST"])
@login_required
def owner_entity_edit(request, pk):
    usecase = OwnerEntityUseCase()
    owner_entity = usecase.get(pk)
    error = None

    if request.method == "POST":
        try:
            data = {
                "owner_name": request.POST.get("owner_name"),
                "owner": request.POST.get("owner") or None,
            }
            if request.POST.get("ultimate_owner"):
                data["ultimate_owner"] = request.POST.get("ultimate_owner")
            usecase.update(pk=pk, **data)
            return redirect("owner-entity-detail", pk=pk)
        except (ValidationError, Exception) as e:
            error = str(e)

    possible_owners = usecase.list().exclude(pk=pk)
    return render(request, "owners/owner_entity_form.html", {
        "owner_entity": owner_entity,
        "possible_owners": possible_owners,
        "possible_ultimate_owners": usecase.list(),
        "error": error,
    })


@require_http_methods(["POST"])
@login_required
def owner_entity_delete(request, pk):
    usecase = OwnerEntityUseCase()
    usecase.delete(pk)
    return redirect("owner-entity-list")
