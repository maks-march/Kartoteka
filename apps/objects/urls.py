from django.urls import path

from apps.objects.views import (
    object_list,
    object_cards,
    object_detail,
    object_create,
    object_edit,
    object_delete,
    object_add_child,
    object_attach_system,
    object_system_edit,
    object_system_delete,
)

urlpatterns = [
    path("", object_list, name="object-list"),
    path("cards/", object_cards, name="object-cards"),
    path("create/", object_create, name="object-create"),
    path("<int:pk>/", object_detail, name="object-detail"),
    path("<int:pk>/edit/", object_edit, name="object-edit"),
    path("<int:pk>/delete/", object_delete, name="object-delete"),
    path("<int:pk>/add-child/", object_add_child, name="object-add-child"),
    path("<int:pk>/attach-system/", object_attach_system, name="object-attach-system"),
    path("system-link/<int:pk>/edit/", object_system_edit, name="object-system-edit"),
    path("system-link/<int:pk>/delete/", object_system_delete, name="object-system-delete"),
]
