from django.urls import path

from apps.system.views import (
    system_list,
    system_cards,
    system_detail,
    system_create,
    system_edit,
    system_delete,
    system_attach_object,
    product_list,
    product_detail,
    product_create,
    product_edit,
    product_delete,
)

urlpatterns = [
    path("", system_list, name="system-list"),
    path("cards/", system_cards, name="system-cards"),

    # Продукты вендоров (объявлены до <int:pk>, чтобы не перехватывались им)
    path("products/", product_list, name="product-list"),
    path("products/create/", product_create, name="product-create"),
    path("products/<int:pk>/", product_detail, name="product-detail"),
    path("products/<int:pk>/edit/", product_edit, name="product-edit"),
    path("products/<int:pk>/delete/", product_delete, name="product-delete"),

    path("<int:pk>/", system_detail, name="system-detail"),
    path("create/", system_create, name="system-create"),
    path("<int:pk>/edit/", system_edit, name="system-edit"),
    path("<int:pk>/delete/", system_delete, name="system-delete"),
    path("<int:pk>/attach-object/", system_attach_object, name="system-attach-object"),
]
