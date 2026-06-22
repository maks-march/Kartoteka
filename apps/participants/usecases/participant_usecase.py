from rest_framework.exceptions import NotFound

from apps.participants.repositories.participant_repository import ParticipantRepository


class ParticipantUseCase:
    def __init__(self, repo=None):
        self.repo = repo or ParticipantRepository()

    def list(self, search=None):
        return self.repo.get_all(search=search)

    def get(self, pk):
        obj = self.repo.get_by_id(pk)
        if not obj:
            raise NotFound("Participant not found")
        return obj

    def create(self, **data):
        return self.repo.create(**data)

    def update(self, pk, **data):
        obj = self.get(pk)
        return self.repo.update(obj, **data)

    def delete(self, pk):
        obj = self.get(pk)
        return self.repo.delete(obj)
