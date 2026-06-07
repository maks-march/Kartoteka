from django.urls import path, include
from rest_framework.routers import DefaultRouter

from objects_app.api.views import ObjectViewSet

router = DefaultRouter()
router.register(r"", ObjectViewSet, basename="object")

app_name = "objects"

urlpatterns = [
    path("", include(router.urls)),
]