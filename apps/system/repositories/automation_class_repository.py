"""Репозиторий доступа к данным классов автоматизации."""
from apps.system.models import AutomationClass


class AutomationClassRepository:
    """Доступ к данным справочника классов автоматизации."""
    def get_all(self):
        """Возвращает все классы автоматизации."""
        return AutomationClass.objects.all().order_by("level", "system_class")

    def get_by_id(self, pk):
        """Возвращает класс автоматизации по id (или None)."""
        return AutomationClass.objects.filter(pk=pk).first()
