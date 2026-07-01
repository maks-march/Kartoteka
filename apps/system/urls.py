from django.urls import path

from apps.system.views import (
    system_list,
    system_cards,
    system_detail,
    system_create,
    system_edit,
    system_delete,
    system_attach_object,
)

urlpatterns = [
    path("", system_list, name="system-list"),
    path("cards/", system_cards, name="system-cards"),
    path("<int:pk>/", system_detail, name="system-detail"),
    path("create/", system_create, name="system-create"),
    path("<int:pk>/edit/", system_edit, name="system-edit"),
    path("<int:pk>/delete/", system_delete, name="system-delete"),
    path("<int:pk>/attach-object/", system_attach_object, name="system-attach-object"),
]
