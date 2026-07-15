"""URL-маршруты REST API систем, классов и продуктов."""
from django.urls import path

from apps.system.api.views import (
    AutomationClassListView,
    SystemListCreateView,
    SystemDetailView,
    SystemAttachObjectView,
    VendorProductListCreateView,
    VendorProductDetailView,
)

urlpatterns = [
    path("classes/", AutomationClassListView.as_view(), name="system-class"),
    path("products/", VendorProductListCreateView.as_view(), name="product-api-list"),
    path("products/<int:pk>/", VendorProductDetailView.as_view(), name="product-api-detail"),
    path("", SystemListCreateView.as_view(), name="system-api-list"),
    path("<int:pk>/", SystemDetailView.as_view(), name="system-api-detail"),
    path(
        "<int:pk>/attach-object/",
        SystemAttachObjectView.as_view(),
        name="system-api-attach-object",
    ),
]
