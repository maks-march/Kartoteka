import re

from apps.system.models import AutomatedSystem


def _as_id_list(value):
    """Нормализует одиночное значение или список в список непустых id."""
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        values = list(value)
    else:
        values = [value]
    return [v for v in values if v not in (None, "", "None")]


class SystemRepository:
    def get_all(self, system_class=None, search=None, obj=None):
        qs = AutomatedSystem.objects.all().select_related("system_class")
        if system_class is not None:
            qs = qs.filter(system_class_id=system_class)
        if search:
            # iregex вместо icontains: на SQLite icontains не игнорирует
            # регистр для не-ASCII символов (кириллицы)
            qs = qs.filter(autosystem_name__iregex=re.escape(search))
        obj_ids = _as_id_list(obj)
        if obj_ids:
            # ИЛИ: системы, привязанные к любому из выбранных объектов
            qs = qs.filter(objectsystem__object_id__in=obj_ids).distinct()
        return qs

    def get_by_id(self, pk):
        return AutomatedSystem.objects.filter(pk=pk).select_related("system_class", "creator_id").first()

    def get_by_creator(self, user, search=None):
        qs = AutomatedSystem.objects.filter(creator_id=user).select_related("system_class")
        if search:
            qs = qs.filter(autosystem_name__iregex=re.escape(search))
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
