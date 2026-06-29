from apps.objects.repositories.object_repository import ObjectRepository
from apps.objects.usecases.validators import ObjectValidator
from common.exceptions import NotFoundException
from rest_framework.exceptions import NotFound


class ObjectUseCase:
    def __init__(self, repo=None):
        self.repo = repo or ObjectRepository()
        self.validator = ObjectValidator()

    def list(self, level=None, search=None, category=None, system=None,
             owner_entity=None, ordering=None):
        return self.repo.get_all(
            level=level,
            search=search,
            category=category,
            system=system,
            owner_entity=owner_entity,
            ordering=ordering,
        )

    def get(self, pk):
        obj = self.repo.get_by_id(pk)
        if not obj:
            raise NotFound("Object not found")
        return obj

    def list_by_user(self, user, search=None):
        return self.repo.get_by_creator(user, search=search)

    # Адресные поля, которые наследуются от родителя (title — исключение, он свой)
    INHERITED_ADDRESS_FIELDS = ("country", "region", "city", "street", "house", "fias_code")

    def get_parent_address_defaults(self, parent_id):
        """Возвращает наследуемые адресные поля родителя для предзаполнения формы."""
        if parent_id in (None, "", "None"):
            return {}
        parent = self.repo.get_by_id(parent_id)
        if not parent:
            return {}
        return {field: getattr(parent, field, "") for field in self.INHERITED_ADDRESS_FIELDS}

    def create(self, user, **data):
        parent_id = data.pop("parent", None)
        category_id = data.pop("category", None)
        owner_entity_id = data.pop("owner_entity", None)
        level = data.get("level")

        self.validator.validate_parent(parent_id, level)
        self.validator.validate_category(category_id, level)
        self.validator.validate_owner_entity(owner_entity_id)
        self.validator.validate_title(data.get("title"), level)

        # Наследование адреса от родителя: заполняем только те адресные поля,
        # которые не переданы явно (или переданы пустыми). title не наследуется.
        if parent_id is not None:
            defaults = self.get_parent_address_defaults(parent_id)
            for field, value in defaults.items():
                if not data.get(field):
                    data[field] = value

        if parent_id is not None:
            data["parent_id"] = parent_id
        if category_id is not None:
            data["category_id"] = category_id
        if owner_entity_id is not None:
            data["owner_entity_id"] = owner_entity_id
        data["creator_id"] = user
        return self.repo.create(**data)

    def update(self, pk, user, **data):
        obj = self.get(pk)
        parent_id = data.pop("parent", "__missing__")
        category_id = data.pop("category", "__missing__")
        owner_entity_id = data.pop("owner_entity", "__missing__")
        level = data.get("level", obj.level)

        if parent_id != "__missing__":
            self.validator.validate_parent(parent_id, level, instance=obj)
            data["parent_id"] = parent_id
        if category_id != "__missing__":
            self.validator.validate_category(category_id, level)
            data["category_id"] = category_id
        if owner_entity_id != "__missing__":
            self.validator.validate_owner_entity(owner_entity_id)
            data["owner_entity_id"] = owner_entity_id

        # Валидация title: уровень определяем по новому значению (если меняется),
        # иначе по текущему уровню объекта.
        if "title" in data:
            effective_level = data.get("level", obj.level)
            self.validator.validate_title(data.get("title"), effective_level)

        if "level" in data and data["level"] != obj.level:
            # При смене уровня перепроверяем текущего родителя и категорию
            current_parent_id = data.get("parent_id", obj.parent_id)
            if current_parent_id is not None:
                self.validator.validate_parent(current_parent_id, data["level"], instance=obj)
            current_category_id = data.get("category_id", obj.category_id)
            if current_category_id is not None:
                self.validator.validate_category(current_category_id, data["level"])

        return self.repo.update(obj, **data)

    def delete(self, pk, user):
        obj = self.get(pk)
        return self.repo.soft_delete(obj)
