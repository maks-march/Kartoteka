from django.urls import path

from apps.system.api.views import (
    AutomationClassListView,
    SystemListCreateView,
    SystemDetailView,
    SystemAttachObjectView,
)

urlpatterns = [
    path("classes/", AutomationClassListView.as_view(), name="system-class"),
    path("", SystemListCreateView.as_view(), name="system-api-list"),
    path("<int:pk>/", SystemDetailView.as_view(), name="system-api-detail"),
    path(
        "<int:pk>/attach-object/",
        SystemAttachObjectView.as_view(),
        name="system-api-attach-object",
    ),
]
