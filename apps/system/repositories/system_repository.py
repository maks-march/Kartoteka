from apps.system.models import AutomatedSystem


class SystemRepository:
    def get_all(self, system_class=None, search=None):
        qs = AutomatedSystem.objects.all().select_related("system_class")
        if system_class is not None:
            qs = qs.filter(system_class_id=system_class)
        if search:
            qs = qs.filter(autosystem_name__icontains=search)
        return qs

    def get_by_id(self, pk):
        return AutomatedSystem.objects.filter(pk=pk).select_related("system_class", "creator_id").first()

    def get_by_creator(self, user, search=None):
        qs = AutomatedSystem.objects.filter(creator_id=user).select_related("system_class")
        if search:
            qs = qs.filter(autosystem_name__icontains=search)
        return qs

    def create(self, **kwargs):
        return AutomatedSystem.objects.create(**kwargs)

    def update(self, instance, **kwargs):
        for key, value in kwargs.items():
            setattr(instance, key, value)
        instance.save()
        return instance

    def delete(self, instance):
        instance.delete()
        return instance
