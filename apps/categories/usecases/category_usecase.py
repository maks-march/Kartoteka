from apps.categories.repositories.category_repository import CategoryRepository
from common.exceptions import NotFoundException, PermissionDeniedError
from rest_framework.exceptions import NotFound


class CategoryUseCase:
    def __init__(self, repo=None):
        self.repo = repo or CategoryRepository()

    def list(self, level=None, search=None):
        return self.repo.get_all(level=level, search=search)

    def list_by_user(self, user, search=None):
        return self.repo.get_by_creator(user, search=search)

    def get(self, pk):
        obj = self.repo.get_by_id(pk)
        if not obj:
            raise NotFound("Category not found")
        return obj

    def create(self, user=None, **data):
        if user is not None:
            data["creator_id"] = user
        return self.repo.create(**data)

    def update(self, pk, user, **data):
        obj = self.get(pk)
        if obj.creator_id != user:
            raise PermissionDeniedError("Только создатель может редактировать запись")
        return self.repo.update(obj, **data)

    def delete(self, pk, user):
        obj = self.get(pk)
        if obj.creator_id != user:
            raise PermissionDeniedError("Только создатель может удалить запись")
        return self.repo.delete(obj)
