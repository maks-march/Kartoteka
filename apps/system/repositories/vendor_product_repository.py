import re

from django.db.models import Count

from apps.system.models import VendorProduct
from common.ordering import apply_ordering


class VendorProductRepository:
    """Доступ к данным продуктов вендоров."""
    ORDERING_FIELDS = {"product_name", "systems_count"}
    DEFAULT_ORDERING = "product_name"

    def get_all(self, search=None, ordering=None):
        qs = VendorProduct.objects.all().select_related("vendor")
        if search:
            # iregex вместо icontains: на SQLite icontains не игнорирует
            # регистр для не-ASCII символов (кириллицы)
            qs = qs.filter(product_name__iregex=re.escape(search))
        qs = qs.annotate(systems_count=Count("systems", distinct=True))
        return apply_ordering(qs, ordering, self.ORDERING_FIELDS, self.DEFAULT_ORDERING)

    def get_by_id(self, pk):
        return VendorProduct.objects.filter(pk=pk).select_related("vendor").first()

    def create(self, **kwargs):
        return VendorProduct.objects.create(**kwargs)

    def update(self, instance, **kwargs):
        for key, value in kwargs.items():
            setattr(instance, key, value)
        instance.save()
        return instance

    def delete(self, instance):
        instance.delete()
        return instance
