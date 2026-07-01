from apps.system.repositories.automation_class_repository import AutomationClassRepository
from rest_framework.exceptions import NotFound


class AutomationClassUseCase:
    """Сценарии работы со справочником классов автоматизации."""
    def __init__(self, repo=None):
        self.repo = repo or AutomationClassRepository()

    def list(self):
        return self.repo.get_all()

    def get(self, pk):
        obj = self.repo.get_by_id(pk)
        if not obj:
            raise NotFound("Automation class not found")
        return obj
