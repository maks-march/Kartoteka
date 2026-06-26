from django.urls import path

from apps.objects.api.views import (
    ObjectListCreateView,
    ObjectDetailView,
    ObjectSystemListCreateView,
    ObjectSystemDetailView,
)

urlpatterns = [
    path("objects/", ObjectListCreateView.as_view(), name="object-api-list"),
    path("objects/<int:pk>/", ObjectDetailView.as_view(), name="object-api-detail"),
    path(
        "object-systems/",
        ObjectSystemListCreateView.as_view(),
        name="object-system-api-list",
    ),
    path(
        "object-systems/<int:pk>/",
        ObjectSystemDetailView.as_view(),
        name="object-system-api-detail",
    ),
]
