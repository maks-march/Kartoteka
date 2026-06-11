from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("", include("apps.core.urls")),
    path("admin/", admin.site.urls),

    path("api/auth/", include("apps.users.api.urls")),
    path("auth/", include("apps.users.urls")),

    path("api/objects/", include("apps.objects.api.urls")),
    path("objects/", include("apps.objects.urls")),

    path("api/categories/", include("apps.categories.api.urls")),
    path("categories/", include("apps.categories.urls")),

    path("api/system/", include("apps.system.api.urls")),
    path("system/", include("apps.system.urls")),
]
