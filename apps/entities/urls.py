"""URL-маршруты HTML-представлений участников рынка."""
from django.urls import path

from apps.entities.views import (
    entity_list,
    entity_cards,
    entity_detail,
    entity_vendor,
    entity_supplier,
    entity_system_integrator,
    entity_engineering,
    entity_full_cycle,
    entity_create,
    entity_edit,
    entity_delete,
)

urlpatterns = [
    path("", entity_list, name="entity-list"),
    path("cards/", entity_cards, name="entity-cards"),
    path("create/", entity_create, name="entity-create"),
    # entity-detail — диспетчер: 302 на типовую страницу по типу участника.
    path("<int:pk>/", entity_detail, name="entity-detail"),
    # Раздельные страницы по типу участника.
    path("<int:pk>/vendor/", entity_vendor, name="entity-vendor"),
    path("<int:pk>/supplier/", entity_supplier, name="entity-supplier"),
    path("<int:pk>/system_integrator/", entity_system_integrator, name="entity-system-integrator"),
    path("<int:pk>/engineering_company/", entity_engineering, name="entity-engineering"),
    path("<int:pk>/full_cycle_vendor/", entity_full_cycle, name="entity-full-cycle"),
    path("<int:pk>/edit/", entity_edit, name="entity-edit"),
    path("<int:pk>/delete/", entity_delete, name="entity-delete"),
]
