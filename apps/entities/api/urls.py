from django.urls import path

from apps.entities.api.views import EntityListCreateView, EntityDetailView

urlpatterns = [
    path("", EntityListCreateView.as_view(), name="entity-api-list"),
    path("<int:pk>/", EntityDetailView.as_view(), name="entity-api-detail"),
]
