from rest_framework.exceptions import NotFound
from django.core.exceptions import ValidationError

from apps.system.repositories.vendor_product_repository import VendorProductRepository
from apps.entities.repositories.entity_repository import EntityRepository


class VendorProductUseCase:
    """Сценарии работы с продуктами вендоров."""
    def __init__(self, repo=None, entity_repo=None):
        self.repo = repo or VendorProductRepository()
        self.entity_repo = entity_repo or EntityRepository()

    def list(self, search=None, ordering=None):
        return self.repo.get_all(search=search, ordering=ordering)

    def get(self, pk):
        obj = self.repo.get_by_id(pk)
        if not obj:
            raise NotFound("Product not found")
        return obj

    def _resolve_vendor(self, data):
        if "vendor" in data:
            vendor_id = data.pop("vendor")
            if vendor_id in (None, "", "None"):
                data["vendor"] = None
            else:
                vendor = self.entity_repo.get_by_id(vendor_id)
                if not vendor:
                    raise ValidationError("Вендор не найден")
                data["vendor"] = vendor
        return data

    def create(self, **data):
        data = self._resolve_vendor(data)
        return self.repo.create(**data)

    def update(self, pk, **data):
        obj = self.get(pk)
        data = self._resolve_vendor(data)
        return self.repo.update(obj, **data)

    def delete(self, pk):
        obj = self.get(pk)
        return self.repo.delete(obj)
