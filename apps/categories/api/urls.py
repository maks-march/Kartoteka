from django.urls import path

from apps.categories.api.views import CategoryListCreateView, CategoryDetailView

urlpatterns = [
    path("categories/", CategoryListCreateView.as_view(), name="category-api-list"),
    path("categories/<int:pk>/", CategoryDetailView.as_view(), name="category-api-detail"),
]
