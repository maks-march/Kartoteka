import re

from django.db.models import Count, Q, Subquery, OuterRef, IntegerField, Value
from django.db.models.functions import Coalesce

from apps.entities.models import Entity
from apps.system.models import AutomationSystem
from common.ordering import apply_ordering


class EntityRepository:
    """Доступ к данным участников рынка."""
    ORDERING_FIELDS = {
        "entity_name", "inn", "entity_type", "registration_date",
        "is_partner", "systems_count", "products_count",
    }
    DEFAULT_ORDERING = "entity_name"

    @staticmethod
    def _annotate(qs):
        """Добавляет счётчики продуктов и связанных систем.

        systems_count — число РАЗЛИЧНЫХ систем, связанных с участником:
        где он integrator или implimentor в ObjectSystem, ЛИБО чей продукт
        принадлежит этому вендору. Считаем подзапросом по AutomationSystem,
        чтобы distinct работал корректно поверх разных связей.
        """
        related_systems = (
            AutomationSystem.objects
            .filter(
                Q(objectsystem__integrator=OuterRef("pk"))
                | Q(objectsystem__implimentor=OuterRef("pk"))
                | Q(product__vendor__entity=OuterRef("pk"))
            )
            .order_by()
            .annotate(_g=Value(1))          # константный ключ группировки
            .values("_g")
            .annotate(c=Count("pk", distinct=True))
            .values("c")
        )
        return qs.annotate(
            products_count=Count("vendor_profile__products", distinct=True),
            systems_count=Coalesce(
                Subquery(related_systems, output_field=IntegerField()), 0
            ),
        )

    def get_all(self, search=None, ordering=None):
        qs = Entity.objects.all()
        if search:
            # iregex вместо icontains: на SQLite icontains не игнорирует
            # регистр для не-ASCII символов (кириллицы)
            qs = qs.filter(entity_name__iregex=re.escape(search))
        qs = self._annotate(qs)
        return apply_ordering(qs, ordering, self.ORDERING_FIELDS, self.DEFAULT_ORDERING)

    def get_by_id(self, pk):
        return self._annotate(Entity.objects.filter(pk=pk)).first()

    def create(self, **kwargs):
        return Entity.objects.create(**kwargs)

    def update(self, instance, **kwargs):
        for key, value in kwargs.items():
            setattr(instance, key, value)
        instance.save()
        return instance

    def delete(self, instance):
        instance.delete()
        return instance
