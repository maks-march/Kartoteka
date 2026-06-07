from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("apps.users.api.urls")),
    path("auth/", include("apps.users.urls")),
    path("api/objects/", include("apps.objects.api.urls")),
    path("objects/", include("apps.objects.urls")),
    path("", include("apps.core.urls")),
]
