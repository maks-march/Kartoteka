"""Сценарии (use cases) работы с классами автоматизации."""
from apps.system.repositories.automation_class_repository import AutomationClassRepository
from rest_framework.exceptions import NotFound


class AutomationClassUseCase:
    """Сценарии работы со справочником классов автоматизации."""
    def __init__(self, repo=None):
        """Инициализирует объект, позволяя подменить зависимости (для тестов)."""
        self.repo = repo or AutomationClassRepository()

    def list(self):
        """Возвращает все классы автоматизации."""
        return self.repo.get_all()

    def get(self, pk):
        """Возвращает класс автоматизации по id или бросает NotFound."""
        obj = self.repo.get_by_id(pk)
        if not obj:
            raise NotFound("Automation class not found")
        return obj
