from django.core.exceptions import ValidationError
from rest_framework.exceptions import NotFound

from apps.owners.repositories.owner_entity_repository import OwnerEntityRepository


_MISSING = "__missing__"


class OwnerEntityUseCase:
    def __init__(self, repo=None):
        self.repo = repo or OwnerEntityRepository()

    def list(self, search=None, ordering=None):
        return self.repo.get_all(search=search, ordering=ordering)

    def get(self, pk):
        obj = self.repo.get_by_id(pk)
        if not obj:
            raise NotFound("Owner entity not found")
        return obj

    def _get_optional_owner(self, pk, field_name):
        if pk in (None, "", "None"):
            return None
        obj = self.repo.get_by_id(pk)
        if not obj:
            raise ValidationError(f"{field_name} не найден")
        return obj

    def _validate_no_owner_cycle(self, owner, instance=None):
        if instance is None or owner is None:
            return

        if owner.pk == instance.pk:
            raise ValidationError("Юридическое лицо не может владеть самим собой")

        current = owner
        visited = set()
        while current:
            if current.pk in visited:
                raise ValidationError("Обнаружен цикл в иерархии юридических лиц")
            visited.add(current.pk)
            if current.owner_id == instance.pk:
                raise ValidationError("Обнаружен цикл: нельзя назначить дочернее юр. лицо владельцем")
            current = current.owner

    def _resolve_ultimate_owner(self, owner, ultimate_owner, ultimate_owner_was_provided):
        # Если корневой владелец явно указан — используем его.
        if ultimate_owner_was_provided:
            return ultimate_owner
        # Иначе при выборе следующего владельца наследуем его корневого владельца.
        if owner is not None:
            return owner.ultimate_owner or owner
        return None

    def create(self, **data):
        owner_id = data.pop("owner", None)
        ultimate_owner_id = data.pop("ultimate_owner", _MISSING)

        owner = self._get_optional_owner(owner_id, "Владелец")
        ultimate_owner_was_provided = ultimate_owner_id != _MISSING
        ultimate_owner = self._get_optional_owner(
            None if ultimate_owner_id == _MISSING else ultimate_owner_id,
            "Корневой владелец",
        )

        data["owner"] = owner
        data["ultimate_owner"] = self._resolve_ultimate_owner(
            owner,
            ultimate_owner,
            ultimate_owner_was_provided,
        )
        return self.repo.create(**data)

    def update(self, pk, **data):
        obj = self.get(pk)
        owner_id = data.pop("owner", _MISSING)
        ultimate_owner_id = data.pop("ultimate_owner", _MISSING)

        if owner_id != _MISSING:
            owner = self._get_optional_owner(owner_id, "Владелец")
            self._validate_no_owner_cycle(owner, instance=obj)
            data["owner"] = owner
        else:
            owner = obj.owner

        if ultimate_owner_id != _MISSING:
            ultimate_owner = self._get_optional_owner(ultimate_owner_id, "Корневой владелец")
            data["ultimate_owner"] = ultimate_owner
        elif owner_id != _MISSING:
            data["ultimate_owner"] = self._resolve_ultimate_owner(
                owner,
                None,
                ultimate_owner_was_provided=False,
            )

        return self.repo.update(obj, **data)

    def delete(self, pk):
        obj = self.get(pk)
        return self.repo.delete(obj)
