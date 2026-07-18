"""Репозиторий доступа к данным продуктов вендоров."""
import re

from django.db.models import Count, Q

from apps.system.models import VendorProduct
from common.ordering import apply_ordering


class VendorProductRepository:
    """Доступ к данным продуктов вендоров."""
    ORDERING_FIELDS = {
        "product_name", "product_type", "version",
        "release_year", "end_of_support",
        "vendor__entity_name", "system_class__system_class",
        "systems_count",
    }
    DEFAULT_ORDERING = "product_name"

    def get_all(self, search=None, system_class=None, ordering=None):
        """Возвращает продукты с фильтрами и сортировкой."""
        qs = VendorProduct.objects.all().select_related("vendor", "system_class")
        if system_class is not None:
            # Класс совпал, если это основной класс продукта ЛИБО он среди
            # классов подсистем (для составных классов вроде MES/MOM/АСУТП).
            qs = qs.filter(
                Q(system_class_id=system_class)
                | Q(subsystem_classes__id=system_class)
            ).distinct()
        if search:
            # iregex вместо icontains: на SQLite icontains не игнорирует
            # регистр для не-ASCII символов (кириллицы)
            qs = qs.filter(product_name__iregex=re.escape(search))
        qs = qs.annotate(systems_count=Count("systems", distinct=True))
        return apply_ordering(qs, ordering, self.ORDERING_FIELDS, self.DEFAULT_ORDERING)

    def get_by_id(self, pk):
        """Возвращает продукт по id (или None)."""
        return (
            VendorProduct.objects.filter(pk=pk)
            .select_related("vendor", "system_class")
            .prefetch_related("subsystem_classes")
            .first()
        )

    def create(self, **kwargs):
        """Создаёт и возвращает новый продукт."""
        subsystem_classes = kwargs.pop("subsystem_classes", None)
        industries = kwargs.pop("industries", None)
        instance = VendorProduct.objects.create(**kwargs)
        if subsystem_classes is not None:
            instance.subsystem_classes.set(subsystem_classes)
        if industries is not None:
            instance.industries.set(industries)
        return instance

    def update(self, instance, **kwargs):
        """Обновляет переданные поля продукта и сохраняет его."""
        subsystem_classes = kwargs.pop("subsystem_classes", "__keep__")
        industries = kwargs.pop("industries", "__keep__")
        for key, value in kwargs.items():
            setattr(instance, key, value)
        instance.save()
        if subsystem_classes != "__keep__":
            instance.subsystem_classes.set(subsystem_classes or [])
        if industries != "__keep__":
            instance.industries.set(industries or [])
        return instance

    def delete(self, instance):
        """Удаляет продукт из БД."""
        instance.delete()
        return instance
