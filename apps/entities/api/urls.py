from django.urls import path

from apps.entities.api.views import (
    EntityListCreateView, EntityDetailView, EngineeringProfileView,
    VendorProductsView, SupplierProductsView,
    SystemIntegratorProfileView, FullCycleProfileView,
)

urlpatterns = [
    path("", EntityListCreateView.as_view(), name="entity-api-list"),
    path("<int:pk>/", EntityDetailView.as_view(), name="entity-api-detail"),
    path("<int:pk>/engineering-profile/", EngineeringProfileView.as_view(),
         name="entity-api-engineering-profile"),
    path("<int:pk>/vendor-products/", VendorProductsView.as_view(),
         name="entity-api-vendor-products"),
    path("<int:pk>/supplier-products/", SupplierProductsView.as_view(),
         name="entity-api-supplier-products"),
    path("<int:pk>/system-integrator-profile/", SystemIntegratorProfileView.as_view(),
         name="entity-api-system-integrator-profile"),
    path("<int:pk>/full-cycle-profile/", FullCycleProfileView.as_view(),
         name="entity-api-full-cycle-profile"),
]
