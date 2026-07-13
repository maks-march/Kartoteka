import re

from django.db.models import Count, Q

from apps.system.models import AutomationSystem
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
    """Доступ к данным автоматизированных систем: выборки с фильтрами,
    сортировкой и счётчиком подключённых объектов, а также CRUD."""
    # Поля, по которым разрешена серверная сортировка.
    ORDERING_FIELDS = {
        "autosystem_name", "system_status",
        "release_year",
        "system_class__system_class", "product__product_name",
        # Аннотированное поле (Count) — количество подключённых объектов.
        "objects_count",
    }
    DEFAULT_ORDERING = "autosystem_name"

    def get_all(self, system_class=None, search=None, obj=None,
                product=None, system_status=None, ordering=None):
        qs = AutomationSystem.objects.all().select_related("system_class", "product")
        if system_class is not None:
            # Класс совпал, если это основной класс системы ЛИБО он есть среди
            # классов подсистем (для составных классов вроде MES/MOM/АСУТП).
            qs = qs.filter(
                Q(system_class_id=system_class)
                | Q(subsystem_classes__id=system_class)
            ).distinct()
        if search:
            # iregex вместо icontains: на SQLite icontains не игнорирует
            # регистр для не-ASCII символов (кириллицы)
            qs = qs.filter(autosystem_name__iregex=re.escape(search))
        obj_ids = _as_id_list(obj)
        if obj_ids:
            # ИЛИ: системы, привязанные к любому из выбранных объектов
            qs = qs.filter(objectsystem__object_id__in=obj_ids).distinct()
        product_ids = _as_id_list(product)
        if product_ids:
            # ИЛИ: системы на любом из выбранных продуктов
            qs = qs.filter(product_id__in=product_ids)
        status_values = _as_id_list(system_status)
        if status_values:
            qs = qs.filter(system_status__in=status_values)
        # Количество подключённых объектов (для списков/карточек)
        qs = qs.annotate(objects_count=Count("objectsystem", distinct=True))
        return apply_ordering(qs, ordering, self.ORDERING_FIELDS, self.DEFAULT_ORDERING)

    def get_by_id(self, pk):
        return (
            AutomationSystem.objects.filter(pk=pk)
            .select_related("system_class", "product", "creator")
            .prefetch_related("subsystem_classes")
            .first()
        )

    def get_by_creator(self, user, search=None):
        qs = AutomationSystem.objects.filter(creator=user).select_related("system_class", "product")
        if search:
            qs = qs.filter(autosystem_name__iregex=re.escape(search))
        return qs

    def create(self, **kwargs):
        # M2M нельзя передать в create() — сохраняем отдельно после создания.
        subsystem_classes = kwargs.pop("subsystem_classes", None)
        instance = AutomationSystem.objects.create(**kwargs)
        if subsystem_classes is not None:
            instance.subsystem_classes.set(subsystem_classes)
        return instance

    def update(self, instance, **kwargs):
        subsystem_classes = kwargs.pop("subsystem_classes", "__keep__")
        for key, value in kwargs.items():
            setattr(instance, key, value)
        instance.save()
        if subsystem_classes != "__keep__":
            instance.subsystem_classes.set(subsystem_classes or [])
        return instance

    def delete(self, instance):
        instance.delete()
        return instance
