"""URL-маршруты HTML-представлений юридических лиц."""
from django.urls import path

from apps.owners.views import (
    owner_entity_list,
    owner_entity_detail,
    owner_entity_create,
    owner_entity_edit,
    owner_entity_attach_object,
    owner_entity_delete,
)

urlpatterns = [
    path("", owner_entity_list, name="owner-entity-list"),
    path("create/", owner_entity_create, name="owner-entity-create"),
    path("<int:pk>/", owner_entity_detail, name="owner-entity-detail"),
    path("<int:pk>/edit/", owner_entity_edit, name="owner-entity-edit"),
    path("<int:pk>/attach-object/", owner_entity_attach_object, name="owner-entity-attach-object"),
    path("<int:pk>/delete/", owner_entity_delete, name="owner-entity-delete"),
]
