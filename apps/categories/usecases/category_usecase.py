from apps.categories.repositories.category_repository import CategoryRepository
from rest_framework.exceptions import NotFound


class CategoryUseCase:
    def __init__(self, repo=None):
        self.repo = repo or CategoryRepository()

    def list(self, level=None, search=None):
        return self.repo.get_all(level=level, search=search)

    def get(self, pk):
        obj = self.repo.get_by_id(pk)
        if not obj:
            raise NotFound("Category not found")
        return obj

    def create(self, **data):
        return self.repo.create(**data)

    def update(self, pk, **data):
        obj = self.get(pk)
        return self.repo.update(obj, **data)

    def delete(self, pk):
        obj = self.get(pk)
        return self.repo.delete(obj)
