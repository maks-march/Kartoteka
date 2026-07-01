import re

from django.db.models import Count

from apps.system.models import AutomatedSystem
from common.ordering import apply_ordering


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
    # Поля, по которым разрешена серверная сортировка.
    ORDERING_FIELDS = {
        "autosystem_name", "version", "system_status", "product_type",
        "release_year", "end_of_support",
        "system_class__system_class", "vendor__participant_name",
    }
    DEFAULT_ORDERING = "autosystem_name"

    def get_all(self, system_class=None, search=None, obj=None,
                vendor=None, system_status=None, product_type=None, ordering=None):
        qs = AutomatedSystem.objects.all().select_related("system_class", "vendor")
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
        vendor_ids = _as_id_list(vendor)
        if vendor_ids:
            # ИЛИ: системы любого из выбранных вендоров
            qs = qs.filter(vendor_id__in=vendor_ids)
        status_values = _as_id_list(system_status)
        if status_values:
            qs = qs.filter(system_status__in=status_values)
        product_types = _as_id_list(product_type)
        if product_types:
            qs = qs.filter(product_type__in=product_types)
        # Количество подключённых объектов (для списков/карточек)
        qs = qs.annotate(objects_count=Count("objectsystem", distinct=True))
        return apply_ordering(qs, ordering, self.ORDERING_FIELDS, self.DEFAULT_ORDERING)

    def get_by_id(self, pk):
        return AutomatedSystem.objects.filter(pk=pk).select_related("system_class", "vendor", "creator_id").first()

    def get_by_creator(self, user, search=None):
        qs = AutomatedSystem.objects.filter(creator_id=user).select_related("system_class", "vendor")
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
