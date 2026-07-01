"""HTML-представления участников рынка."""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ValidationError

from apps.participants.usecases.participant_usecase import ParticipantUseCase


@require_http_methods(["GET"])
def participant_list(request):
    search = request.GET.get("search") or None
    ordering = request.GET.getlist("ordering") or None
    usecase = ParticipantUseCase()
    participants = usecase.list(search=search, ordering=ordering)
    return render(request, "participants/participant_list.html", {
        "participants": participants,
        "ordering": ordering or [],
    })


@require_http_methods(["GET"])
def participant_detail(request, pk):
    usecase = ParticipantUseCase()
    participant = usecase.get(pk)
    vendor_systems = participant.vendor_systems.select_related("system_class")
    integrated_links = participant.integrated_object_systems.select_related("object", "system")
    implemented_links = participant.implemented_object_systems.select_related("object", "system")
    return render(request, "participants/participant_detail.html", {
        "participant": participant,
        "vendor_systems": vendor_systems,
        "integrated_links": integrated_links,
        "implemented_links": implemented_links,
    })


@require_http_methods(["GET", "POST"])
@login_required
def participant_create(request):
    error = None
    if request.method == "POST":
        usecase = ParticipantUseCase()
        try:
            participant = usecase.create(
                participant_name=request.POST.get("participant_name"),
            )
            return redirect("participant-detail", pk=participant.pk)
        except (ValidationError, Exception) as e:
            error = str(e)
    return render(request, "participants/participant_form.html", {"error": error})


@require_http_methods(["GET", "POST"])
@login_required
def participant_edit(request, pk):
    usecase = ParticipantUseCase()
    participant = usecase.get(pk)
    error = None

    if request.method == "POST":
        try:
            usecase.update(
                pk=pk,
                participant_name=request.POST.get("participant_name"),
            )
            return redirect("participant-detail", pk=pk)
        except (ValidationError, Exception) as e:
            error = str(e)

    return render(request, "participants/participant_form.html", {
        "participant": participant,
        "error": error,
    })


@require_http_methods(["POST"])
@login_required
def participant_delete(request, pk):
    usecase = ParticipantUseCase()
    usecase.delete(pk)
    return redirect("participant-list")
