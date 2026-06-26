import re

from apps.objects.models import Object


def _as_id_list(value):
    """Нормализует одиночное значение или список в список непустых id."""
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        values = list(value)
    else:
        values = [value]
    return [v for v in values if v not in (None, "", "None")]


class ObjectRepository:
    def get_all(self, level=None, search=None, category=None, system=None, owner_entity=None):
        qs = Object.objects.filter(is_deleted=False).select_related("parent", "category", "owner_entity")
        if level is not None:
            qs = qs.filter(level=level)
        if search:
            # iregex вместо icontains: на SQLite icontains не игнорирует
            # регистр для не-ASCII символов (кириллицы)
            qs = qs.filter(name__iregex=re.escape(search))
        category_ids = _as_id_list(category)
        if category_ids:
            # ИЛИ: объекты с любой из выбранных категорий
            qs = qs.filter(category_id__in=category_ids)
        system_ids = _as_id_list(system)
        if system_ids:
            # ИЛИ: объекты, к которым привязана любая из выбранных систем
            qs = qs.filter(objectsystem__system_id__in=system_ids).distinct()
        owner_entity_ids = _as_id_list(owner_entity)
        if owner_entity_ids:
            # Иерархический фильтр: к выбранным юр. лицам добавляем все их
            # дочерние юр. лица (на любую глубину), чтобы в выборку попадали и
            # объекты, которыми владеют потомки указанного владельца.
            from apps.owners.repositories.owner_entity_repository import (
                OwnerEntityRepository,
            )

            owner_entity_ids = OwnerEntityRepository().get_descendant_ids(
                owner_entity_ids
            )
            # ИЛИ: объекты, принадлежащие любому из выбранных юр. лиц или их потомкам
            qs = qs.filter(owner_entity_id__in=owner_entity_ids)
        return qs

    def get_by_id(self, pk):
        return (
            Object.objects.filter(pk=pk, is_deleted=False)
            .select_related("parent", "category", "owner_entity", "creator_id")
            .prefetch_related("children")
            .first()
        )

    def get_by_creator(self, user, search=None):
        qs = Object.objects.filter(is_deleted=False, creator_id=user).select_related("parent", "category", "owner_entity")
        if search:
            qs = qs.filter(name__iregex=re.escape(search))
        return qs

    def create(self, **kwargs):
        return Object.objects.create(**kwargs)

    def update(self, instance, **kwargs):
        for key, value in kwargs.items():
            setattr(instance, key, value)
        instance.save()
        return instance

    def soft_delete(self, instance):
        instance.is_deleted = True
        instance.save()
        return instance
