from apps.objects.repositories.object_repository import ObjectRepository
from apps.objects.usecases.validators import ObjectValidator
from rest_framework.exceptions import NotFound


class ObjectUseCase:
    def __init__(self, repo=None):
        self.repo = repo or ObjectRepository()
        self.validator = ObjectValidator()

    def list(self, level=None, search=None, category=None):
        return self.repo.get_all(level=level, search=search, category=category)

    def get(self, pk):
        obj = self.repo.get_by_id(pk)
        if not obj:
            raise NotFound("Object not found")
        return obj

    def list_by_user(self, user, search=None):
        return self.repo.get_by_creator(user, search=search)

    def create(self, user, **data):
        parent_id = data.pop("parent", None)
        category_id = data.pop("category", None)
        level = data.get("level")

        self.validator.validate_parent(parent_id, level)
        self.validator.validate_category(category_id, level)

        if parent_id is not None:
            data["parent_id"] = parent_id
        if category_id is not None:
            data["category_id"] = category_id
        data["created_by"] = user
        return self.repo.create(**data)

    def update(self, pk, user, **data):
        obj = self.get(pk)
        parent_id = data.pop("parent", "__missing__")
        category_id = data.pop("category", "__missing__")
        level = data.get("level", obj.level)

        if parent_id != "__missing__":
            self.validator.validate_parent(parent_id, level, instance=obj)
            data["parent_id"] = parent_id
        if category_id != "__missing__":
            self.validator.validate_category(category_id, level)
            data["category_id"] = category_id

        if "level" in data and data["level"] != obj.level:
            # При смене уровня перепроверяем текущего родителя и категорию
            current_parent_id = data.get("parent_id", obj.parent_id)
            if current_parent_id is not None:
                self.validator.validate_parent(current_parent_id, data["level"], instance=obj)
            current_category_id = data.get("category_id", obj.category_id)
            if current_category_id is not None:
                self.validator.validate_category(current_category_id, data["level"])

        return self.repo.update(obj, **data)

    def delete(self, pk):
        obj = self.get(pk)
        return self.repo.soft_delete(obj)
