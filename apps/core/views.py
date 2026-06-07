from django.shortcuts import render
from django.views.decorators.http import require_http_methods


@require_http_methods(["GET"])
def hub(request):
    return render(request, "core/hub.html")
