from django.urls import path

from apps.participants.views import (
    participant_list,
    participant_detail,
    participant_create,
    participant_edit,
    participant_delete,
)

urlpatterns = [
    path("", participant_list, name="participant-list"),
    path("create/", participant_create, name="participant-create"),
    path("<int:pk>/", participant_detail, name="participant-detail"),
    path("<int:pk>/edit/", participant_edit, name="participant-edit"),
    path("<int:pk>/delete/", participant_delete, name="participant-delete"),
]
