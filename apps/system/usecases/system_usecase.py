from apps.system.repositories.system_repository import SystemRepository
from apps.system.repositories.automation_class_repository import AutomationClassRepository
from apps.system.repositories.vendor_product_repository import VendorProductRepository
from rest_framework.exceptions import NotFound
from django.core.exceptions import ValidationError


class SystemUseCase:
    """Сценарии работы с автоматизированными системами: список с фильтрами и
    сортировкой, CRUD, разбор JSON-полей и связанного продукта."""
    def __init__(self, repo=None, class_repo=None, product_repo=None):
        self.repo = repo or SystemRepository()
        self.class_repo = class_repo or AutomationClassRepository()
        self.product_repo = product_repo or VendorProductRepository()

    def list(self, system_class=None, search=None, obj=None,
             product=None, system_status=None, ordering=None):
        return self.repo.get_all(
            system_class=system_class,
            search=search,
            obj=obj,
            product=product,
            system_status=system_status,
            ordering=ordering,
        )

    def list_by_user(self, user, search=None):
        return self.repo.get_by_creator(user, search=search)

    def get(self, pk):
        obj = self.repo.get_by_id(pk)
        if not obj:
            raise NotFound("System not found")
        return obj

    def _get_optional_product(self, pk):
        if pk in (None, "", "None"):
            return None
        product = self.product_repo.get_by_id(pk)
        if not product:
            raise ValidationError("Продукт не найден")
        return product

    def create(self, user=None, **data):
        class_id = data.get("system_class")
        if class_id is not None and not self.class_repo.get_by_id(class_id):
            raise ValidationError("Automation class not found")
        data['system_class'] = self.class_repo.get_by_id(class_id)

        product_id = data.pop("product", None)
        data["product"] = self._get_optional_product(product_id)

        if user is not None:
            data['creator_id'] = user
        return self.repo.create(**data)

    def update(self, pk, user, **data):
        obj = self.get(pk)
        # system_class трогаем только если он передан (для частичного обновления).
        if "system_class" in data:
            class_id = data.get("system_class")
            klass = self.class_repo.get_by_id(class_id) if class_id is not None else None
            if klass is None:
                raise ValidationError("Automation class not found")
            data["system_class"] = klass

        if "product" in data:
            product_id = data.pop("product")
            data["product"] = self._get_optional_product(product_id)

        return self.repo.update(obj, **data)

    def delete(self, pk, user):
        obj = self.get(pk)
        return self.repo.delete(obj)
