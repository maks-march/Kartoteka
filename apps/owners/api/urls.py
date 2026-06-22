from django.urls import path

from apps.owners.api.views import OwnerEntityListCreateView, OwnerEntityDetailView

urlpatterns = [
    path("", OwnerEntityListCreateView.as_view(), name="owner-entity-api-list"),
    path("<int:pk>/", OwnerEntityDetailView.as_view(), name="owner-entity-api-detail"),
]
