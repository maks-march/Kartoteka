"""Сценарии (use cases) работы с категориями объектов."""
from apps.categories.repositories.category_repository import CategoryRepository
from rest_framework.exceptions import NotFound


class CategoryUseCase:
    """Сценарии работы с категориями объектов."""
    def __init__(self, repo=None):
        """Инициализирует объект, позволяя подменить зависимости (для тестов)."""
        self.repo = repo or CategoryRepository()

    def list(self, level=None, search=None, ordering=None):
        """Возвращает категории с учётом фильтров и сортировки."""
        return self.repo.get_all(level=level, search=search, ordering=ordering)

    def list_by_user(self, user, search=None):
        """Возвращает категории, созданные пользователем."""
        return self.repo.get_by_creator(user, search=search)

    def get(self, pk):
        """Возвращает категорию по id или бросает NotFound."""
        obj = self.repo.get_by_id(pk)
        if not obj:
            raise NotFound("Category not found")
        return obj

    def create(self, user=None, **data):
        """Создаёт категорию, проставляя автора."""
        if user is not None:
            data["creator"] = user
        return self.repo.create(**data)

    def update(self, pk, user, **data):
        """Обновляет категорию переданными полями."""
        obj = self.get(pk)
        return self.repo.update(obj, **data)

    def delete(self, pk, user):
        """Удаляет категорию по id."""
        obj = self.get(pk)
        return self.repo.delete(obj)
