from django.urls import path

from apps.categories.views import category_list, category_create, category_edit, category_delete, category_detail

urlpatterns = [
    path("", category_list, name="category-list"),
    path("create/", category_create, name="category-create"),
    path("<int:pk>/", category_detail, name="category-detail"),
    path("<int:pk>/edit/", category_edit, name="category-edit"),
    path("<int:pk>/delete/", category_delete, name="category-delete"),
]
