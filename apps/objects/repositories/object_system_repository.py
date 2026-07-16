"""Репозиторий доступа к данным связей «система на объекте»."""
from apps.objects.models import ObjectSystem


class ObjectSystemRepository:
    """Доступ к данным связей «система на объекте» (ObjectSystem)."""

    def get_for_object(self, obj):
        """Возвращает связи (системы), привязанные к объекту, с подгрузкой связей."""
        return (
            ObjectSystem.objects.filter(object=obj)
            .select_related(
                "system", "system__system_class", "system__product",
                "system__product__vendor__entity", "implementor",
            )
            .order_by("system__autosystem_name")
        )

    def get_for_system(self, system):
        """Возвращает связи (объекты), к которым привязана система."""
        return (
            ObjectSystem.objects.filter(system=system)
            .select_related("object", "object__category", "implementor")
            .order_by("object__hierarchy_level", "object__object_name")
        )

    def exists(self, obj, system, exclude_pk=None):
        """Проверяет наличие связи (объект, система); exclude_pk — исключить свою запись."""
        qs = ObjectSystem.objects.filter(object=obj, system=system)
        if exclude_pk is not None:
            qs = qs.exclude(pk=exclude_pk)
        return qs.exists()

    def get_by_id(self, pk):
        """Возвращает связь по id с подгруженными связями (или None)."""
        return (
            ObjectSystem.objects.filter(pk=pk)
            .select_related("object", "system", "system__system_class", "system__product", "implementor")
            .first()
        )

    def create(self, **kwargs):
        """Создаёт и возвращает новую связь."""
        return ObjectSystem.objects.create(**kwargs)

    def update(self, instance, **kwargs):
        """Обновляет переданные поля связи и сохраняет её."""
        for key, value in kwargs.items():
            setattr(instance, key, value)
        instance.save()
        return instance

    def delete(self, instance):
        """Удаляет связь из БД."""
        instance.delete()
        return instance
