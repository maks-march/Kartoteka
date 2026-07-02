from django.urls import path

from apps.entities.views import (
    entity_list,
    entity_cards,
    entity_detail,
    entity_create,
    entity_edit,
    entity_delete,
)

urlpatterns = [
    path("", entity_list, name="entity-list"),
    path("cards/", entity_cards, name="entity-cards"),
    path("create/", entity_create, name="entity-create"),
    path("<int:pk>/", entity_detail, name="entity-detail"),
    path("<int:pk>/edit/", entity_edit, name="entity-edit"),
    path("<int:pk>/delete/", entity_delete, name="entity-delete"),
]
