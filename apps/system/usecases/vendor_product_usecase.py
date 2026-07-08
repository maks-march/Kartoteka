from rest_framework.exceptions import NotFound
from django.core.exceptions import ValidationError

from apps.system.repositories.vendor_product_repository import VendorProductRepository
from apps.system.repositories.automation_class_repository import AutomationClassRepository
from apps.entities.repositories.entity_repository import EntityRepository


class VendorProductUseCase:
    """Сценарии работы с продуктами вендоров."""
    def __init__(self, repo=None, entity_repo=None, class_repo=None):
        self.repo = repo or VendorProductRepository()
        self.entity_repo = entity_repo or EntityRepository()
        self.class_repo = class_repo or AutomationClassRepository()

    def list(self, search=None, system_class=None, ordering=None):
        return self.repo.get_all(search=search, system_class=system_class, ordering=ordering)

    def get(self, pk):
        obj = self.repo.get_by_id(pk)
        if not obj:
            raise NotFound("Product not found")
        return obj

    def _resolve_vendor(self, data):
        """Значение поля vendor — это id УЧАСТНИКА (Entity). Продукт привязывается
        к его VendorProfile (создаётся при необходимости). Профиль есть только у
        вендора / вендора полного цикла — иначе привязка запрещена.
        """
        if "vendor" in data:
            vendor_id = data.pop("vendor")
            if vendor_id in (None, "", "None"):
                data["vendor"] = None
            else:
                entity = self.entity_repo.get_by_id(vendor_id)
                if not entity:
                    raise ValidationError("Вендор не найден")
                if not entity.is_vendor_type:
                    raise ValidationError(
                        "Продукт можно привязать только к вендору или вендору полного цикла"
                    )
                from apps.entities.models import VendorProfile
                profile, _ = VendorProfile.objects.get_or_create(entity=entity)
                data["vendor"] = profile
        return data

    def _get_class(self, class_id):
        if class_id in (None, "", "None"):
            return None
        klass = self.class_repo.get_by_id(class_id)
        if not klass:
            raise ValidationError("Класс системы не найден")
        return klass

    def _resolve_subsystem_classes(self, raw_ids, primary_class):
        """Классы-подсистемы для составного основного класса продукта.

        - несоставной основной класс → подсистем нет (очищаем);
        - составной → переданные классы + авто-подстановка primary_class.includes
          (напр. MOM ⇒ MES).
        """
        if primary_class is None or not primary_class.is_composite:
            return []
        classes, seen = [], set()
        for i in (raw_ids or []):
            if i in (None, "", "None"):
                continue
            klass = self.class_repo.get_by_id(int(i))
            if not klass:
                raise ValidationError(f"Класс подсистемы не найден: {i}")
            if klass.pk not in seen:
                seen.add(klass.pk)
                classes.append(klass)
        if primary_class.includes_id and primary_class.includes_id not in seen:
            included = self.class_repo.get_by_id(primary_class.includes_id)
            if included:
                classes.append(included)
        return classes

    def create(self, **data):
        data = self._resolve_vendor(data)
        primary_class = self._get_class(data.get("system_class")) if "system_class" in data else None
        if "system_class" in data:
            data["system_class"] = primary_class
        raw_subsystems = data.pop("subsystem_classes", None)
        data["subsystem_classes"] = self._resolve_subsystem_classes(raw_subsystems, primary_class)
        return self.repo.create(**data)

    def update(self, pk, **data):
        obj = self.get(pk)
        data = self._resolve_vendor(data)

        primary_class = obj.system_class
        if "system_class" in data:
            primary_class = self._get_class(data.get("system_class"))
            data["system_class"] = primary_class

        # Подсистемы пересчитываем, если переданы ИЛИ сменился основной класс
        # (смена на несоставной класс очищает подсистемы).
        if "subsystem_classes" in data or "system_class" in data:
            raw_subsystems = data.pop("subsystem_classes", None)
            data["subsystem_classes"] = self._resolve_subsystem_classes(raw_subsystems, primary_class)

        return self.repo.update(obj, **data)

    def delete(self, pk):
        obj = self.get(pk)
        return self.repo.delete(obj)
