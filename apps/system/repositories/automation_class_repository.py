from apps.system.models import AutomationClass


class AutomationClassRepository:
    def get_all(self):
        return AutomationClass.objects.all().order_by("level", "system_class")

    def get_by_id(self, pk):
        return AutomationClass.objects.filter(pk=pk).first()
