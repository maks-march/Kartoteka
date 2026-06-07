from django.urls import path

from apps.objects.views import (
    object_list,
    object_detail,
    object_create,
    object_edit,
    object_delete,
    object_add_child,
)

urlpatterns = [
    path("", object_list, name="object-list"),
    path("create/", object_create, name="object-create"),
    path("<int:pk>/", object_detail, name="object-detail"),
    path("<int:pk>/edit/", object_edit, name="object-edit"),
    path("<int:pk>/delete/", object_delete, name="object-delete"),
    path("<int:pk>/add-child/", object_add_child, name="object-add-child"),
]
