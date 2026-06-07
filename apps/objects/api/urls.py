from django.urls import path

from apps.objects.api.views import ObjectListCreateView, ObjectDetailView

urlpatterns = [
    path("objects/", ObjectListCreateView.as_view(), name="object-list"),
    path("objects/<int:pk>/", ObjectDetailView.as_view(), name="object-detail"),
]
