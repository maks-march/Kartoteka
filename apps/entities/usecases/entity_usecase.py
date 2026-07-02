from rest_framework.exceptions import NotFound

from apps.entities.repositories.entity_repository import EntityRepository


class EntityUseCase:
    """Сценарии работы с участниками рынка."""
    def __init__(self, repo=None):
        self.repo = repo or EntityRepository()

    def list(self, search=None, ordering=None):
        return self.repo.get_all(search=search, ordering=ordering)

    def get(self, pk):
        obj = self.repo.get_by_id(pk)
        if not obj:
            raise NotFound("Entity not found")
        return obj

    def create(self, **data):
        return self.repo.create(**data)

    def update(self, pk, **data):
        obj = self.get(pk)
        return self.repo.update(obj, **data)

    def delete(self, pk):
        obj = self.get(pk)
        return self.repo.delete(obj)
