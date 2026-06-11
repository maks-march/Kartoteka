from django.urls import path

from apps.system.api.views import (
    AutomationClassListView,
    SystemListCreateView,
    SystemDetailView,
)

urlpatterns = [
    path("classes/", AutomationClassListView.as_view(), name="system-class"),
    path("", SystemListCreateView.as_view(), name="system-api-list"),
    path("<int:pk>/", SystemDetailView.as_view(), name="system-api-detail"),
]
