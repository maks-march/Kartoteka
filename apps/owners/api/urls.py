"""URL-маршруты REST API юридических лиц."""
from django.urls import path

from apps.owners.api.views import (
    OwnerEntityListCreateView,
    OwnerEntityDetailView,
    OwnerEntityAttachObjectView,
)

urlpatterns = [
    path("", OwnerEntityListCreateView.as_view(), name="owner-entity-api-list"),
    path("<int:pk>/", OwnerEntityDetailView.as_view(), name="owner-entity-api-detail"),
    path(
        "<int:pk>/attach-object/",
        OwnerEntityAttachObjectView.as_view(),
        name="owner-entity-api-attach-object",
    ),
]
