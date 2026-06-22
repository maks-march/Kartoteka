from django.core.exceptions import ValidationError

from apps.objects.repositories.object_system_repository import ObjectSystemRepository
from apps.objects.repositories.object_repository import ObjectRepository
from apps.system.repositories.system_repository import SystemRepository
from apps.participants.repositories.participant_repository import ParticipantRepository
from common.exceptions import NotFoundException
from rest_framework.exceptions import NotFound


class ObjectSystemUseCase:
    def __init__(self, repo=None, object_repo=None, system_repo=None, participant_repo=None):
        self.repo = repo or ObjectSystemRepository()
        self.object_repo = object_repo or ObjectRepository()
        self.system_repo = system_repo or SystemRepository()
        self.participant_repo = participant_repo or ParticipantRepository()

    def list_for_object(self, obj):
        return self.repo.get_for_object(obj)

    def list_for_system(self, system):
        return self.repo.get_for_system(system)

    def _get_optional_participant(self, pk, field_name):
        if pk in (None, "", "None"):
            return None
        participant = self.participant_repo.get_by_id(pk)
        if not participant:
            raise ValidationError(f"{field_name} не найден")
        return participant

    def _resolve_participants(self, data):
        if "integrator" in data:
            integrator_id = data.pop("integrator")
            data["integrator"] = self._get_optional_participant(integrator_id, "Интегратор")
        if "implimentor" in data:
            implimentor_id = data.pop("implimentor")
            data["implimentor"] = self._get_optional_participant(implimentor_id, "Исполнитель внедрения")
        return data

    def attach(self, object_pk=None, system_pk=None, **data):
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

        data = self._resolve_participants(data)
        return self.repo.create(object=obj, system=system, **data)

    def get(self, pk):
        link = self.repo.get_by_id(pk)
        if not link:
            raise NotFoundException("Привязка не найдена")
        return link

    def update(self, pk, object_pk=None, system_pk=None, **data):
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

        data = self._resolve_participants(data)
        return self.repo.update(link, object=obj, system=system, **data)

    def detach(self, pk):
        link = self.get(pk)
        return self.repo.delete(link)
