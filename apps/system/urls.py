from django.urls import path

from apps.system.views import system_list, system_detail, system_create, system_edit, system_delete

urlpatterns = [
    path("", system_list, name="system-list"),
    path("<int:pk>/", system_detail, name="system-detail"),
    path("create/", system_create, name="system-create"),
    path("<int:pk>/edit/", system_edit, name="system-edit"),
    path("<int:pk>/delete/", system_delete, name="system-delete"),
]
