from django.urls import path

from apps.participants.api.views import ParticipantListCreateView, ParticipantDetailView

urlpatterns = [
    path("", ParticipantListCreateView.as_view(), name="participant-api-list"),
    path("<int:pk>/", ParticipantDetailView.as_view(), name="participant-api-detail"),
]
