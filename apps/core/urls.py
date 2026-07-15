"""URL-маршруты общего приложения."""
from django.urls import path

from apps.core.views import (
    hub
)

urlpatterns = [
    path("", hub, name="hub"),
]