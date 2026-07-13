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

    def _resolve_subsystem_classes(self, raw_ids, primary_class):
        """Готовит набор классов-подсистем для составного основного класса.

        Правила:
        - если основной класс не составной (is_composite=False) → подсистем нет
          (очищаем), даже если что-то передали;
        - если составной → берём переданные классы + автоматически добавляем
          класс из primary_class.includes (напр. MOM ⇒ MES).
        """
        if primary_class is None or not primary_class.is_composite:
            return []

        ids = []
        for i in (raw_ids or []):
            if i in (None, "", "None"):
                continue
            ids.append(int(i))

        classes = []
        seen = set()
        for cid in ids:
            klass = self.class_repo.get_by_id(cid)
            if not klass:
                raise ValidationError(f"Класс подсистемы не найден: {cid}")
            if klass.pk not in seen:
                seen.add(klass.pk)
                classes.append(klass)

        # Авто-подстановка включаемого класса (MOM ⇒ MES).
        if primary_class.includes_id and primary_class.includes_id not in seen:
            included = self.class_repo.get_by_id(primary_class.includes_id)
            if included:
                seen.add(included.pk)
                classes.append(included)

        return classes

    def create(self, user=None, **data):
        class_id = data.get("system_class")
        primary_class = self.class_repo.get_by_id(class_id) if class_id is not None else None
        if primary_class is None:
            raise ValidationError("Automation class not found")
        data['system_class'] = primary_class

        product_id = data.pop("product", None)
        data["product"] = self._get_optional_product(product_id)

        raw_subsystems = data.pop("subsystem_classes", None)
        data["subsystem_classes"] = self._resolve_subsystem_classes(raw_subsystems, primary_class)

        if user is not None:
            data['creator'] = user
        return self.repo.create(**data)

    def update(self, pk, user, **data):
        obj = self.get(pk)

        # system_class трогаем только если он передан (для частичного обновления).
        primary_class = obj.system_class
        if "system_class" in data:
            class_id = data.get("system_class")
            klass = self.class_repo.get_by_id(class_id) if class_id is not None else None
            if klass is None:
                raise ValidationError("Automation class not found")
            data["system_class"] = klass
            primary_class = klass

        if "product" in data:
            product_id = data.pop("product")
            data["product"] = self._get_optional_product(product_id)

        # Подсистемы пересчитываем, если их передали ИЛИ сменили основной класс
        # (смена класса на несоставной очищает подсистемы — правило 4).
        if "subsystem_classes" in data or "system_class" in data:
            raw_subsystems = data.pop("subsystem_classes", None)
            data["subsystem_classes"] = self._resolve_subsystem_classes(
                raw_subsystems, primary_class
            )

        return self.repo.update(obj, **data)

    def delete(self, pk, user):
        obj = self.get(pk)
        return self.repo.delete(obj)
