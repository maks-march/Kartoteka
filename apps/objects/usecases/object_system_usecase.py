"""Сценарии (use cases) управления связью «система на объекте».

Отвечают за привязку/изменение/отвязку систем к объектам с проверкой
существования участников и уникальности связи (объект, система).
"""
from django.core.exceptions import ValidationError

from apps.objects.repositories.object_system_repository import ObjectSystemRepository
from apps.objects.repositories.object_repository import ObjectRepository
from apps.system.repositories.system_repository import SystemRepository
from apps.entities.repositories.entity_repository import EntityRepository
from common.exceptions import NotFoundException
from rest_framework.exceptions import NotFound


class ObjectSystemUseCase:
    """Сценарии управления связью «система на объекте» (привязка, изменение,
    отвязка) с проверкой участников и уникальности связи."""
    def __init__(self, repo=None, object_repo=None, system_repo=None, entity_repo=None):
        """Инициализирует use case; репозитории можно подменить (для тестов)."""
        self.repo = repo or ObjectSystemRepository()
        self.object_repo = object_repo or ObjectRepository()
        self.system_repo = system_repo or SystemRepository()
        self.entity_repo = entity_repo or EntityRepository()

    def list_for_object(self, obj):
        """Возвращает связи (системы), привязанные к данному объекту."""
        return self.repo.get_for_object(obj)

    def list_for_system(self, system):
        """Возвращает связи (объекты), к которым привязана данная система."""
        return self.repo.get_for_system(system)

    def _get_optional_entity(self, pk, field_name):
        """Разрешает id участника в объект Entity (вспомогательный).

        Возвращает None для пустого значения, бросает ValidationError, если
        участник с таким id не найден. Используется для необязательных FK
        (например, исполнитель внедрения).
        """
        if pk in (None, "", "None"):
            return None
        entity = self.entity_repo.get_by_id(pk)
        if not entity:
            raise ValidationError(f"{field_name} не найден")
        return entity

    def _resolve_entities(self, data):
        """Заменяет id участников в data на объекты Entity (вспомогательный).

        Нужен, чтобы attach/update принимали как id, так и объекты, а в
        репозиторий уходили уже разрешённые связи.
        """
        if "implementor" in data:
            implementor_id = data.pop("implementor")
            implementor = self._get_optional_entity(implementor_id, "Исполнитель внедрения")
            # Исполнителем внедрения может быть только интегратор, инжиниринговая
            # компания или вендор полного цикла — не вендор и не поставщик.
            if implementor is not None and not implementor.can_implement:
                raise ValidationError(
                    "Исполнителем внедрения не может быть вендор или поставщик — "
                    "только системный интегратор, инжиниринговая компания или "
                    "вендор полного цикла"
                )
            data["implementor"] = implementor
        return data

    def attach(self, object_pk=None, system_pk=None, **data):
        """Привязывает систему к объекту, проверяя существование и уникальность связи."""
        if object_pk is None:
            object_pk = data.pop("object", None)
        if system_pk is None:
            system_pk = data.pop("system", None)

        if object_pk is None:
            raise ValidationError("Необходимо выбрать объект")
        if system_pk is None:
            raise ValidationError("Необходимо выбрать систему")

        obj = self.object_repo.get_by_id(object_pk)
        if not obj:
            raise NotFound("Object not found")

        system = self.system_repo.get_by_id(system_pk)
        if not system:
            raise ValidationError("Система не найдена")

        if self.repo.exists(obj, system):
            raise ValidationError("Эта система уже привязана к объекту")

        data = self._resolve_entities(data)
        return self.repo.create(object=obj, system=system, **data)

    def get(self, pk):
        """Возвращает связь по id или бросает NotFoundException."""
        link = self.repo.get_by_id(pk)
        if not link:
            raise NotFoundException("Привязка не найдена")
        return link

    def update(self, pk, object_pk=None, system_pk=None, **data):
        """Обновляет связь: при смене объекта/системы проверяет уникальность пары."""
        link = self.get(pk)

        obj = link.object
        if object_pk is not None and object_pk != link.object_id:
            obj = self.object_repo.get_by_id(object_pk)
            if not obj:
                raise ValidationError("Объект не найден")

        system = link.system
        if system_pk is not None and system_pk != link.system_id:
            system = self.system_repo.get_by_id(system_pk)
            if not system:
                raise ValidationError("Система не найдена")

        if self.repo.exists(obj, system, exclude_pk=link.pk):
            raise ValidationError("Эта система уже привязана к объекту")

        data = self._resolve_entities(data)
        return self.repo.update(link, object=obj, system=system, **data)

    def detach(self, pk):
        """Отвязывает систему от объекта (удаляет связь)."""
        link = self.get(pk)
        return self.repo.delete(link)
