from apps.objects.models import ObjectSystem


class ObjectSystemRepository:
    """Доступ к данным связей «система на объекте»."""
    def get_for_object(self, obj):
        return (
            ObjectSystem.objects.filter(object=obj)
            .select_related("system", "system__system_class", "system__product", "integrator", "implimentor")
            .order_by("system__autosystem_name")
        )

    def get_for_system(self, system):
        return (
            ObjectSystem.objects.filter(system=system, object__is_deleted=False)
            .select_related("object", "object__category", "integrator", "implimentor")
            .order_by("object__level", "object__name")
        )

    def exists(self, obj, system, exclude_pk=None):
        qs = ObjectSystem.objects.filter(object=obj, system=system)
        if exclude_pk is not None:
            qs = qs.exclude(pk=exclude_pk)
        return qs.exists()

    def get_by_id(self, pk):
        return (
            ObjectSystem.objects.filter(pk=pk)
            .select_related("object", "system", "system__system_class", "system__product", "integrator", "implimentor")
            .first()
        )

    def create(self, **kwargs):
        return ObjectSystem.objects.create(**kwargs)

    def update(self, instance, **kwargs):
        for key, value in kwargs.items():
            setattr(instance, key, value)
        instance.save()
        return instance

    def delete(self, instance):
        instance.delete()
        return instance
