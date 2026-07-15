"""HTML-представления общего приложения (главная страница-хаб)."""
from django.shortcuts import render
from django.views.decorators.http import require_http_methods


@require_http_methods(["GET"])
def hub(request):
    """Главная страница-хаб с навигацией по разделам."""
    return render(request, "core/hub.html")
