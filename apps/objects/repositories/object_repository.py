"""Репозиторий доступа к данным объектов производства.

Инкапсулирует запросы ORM: выборки с фильтрами и сортировкой, счётчик
подключённых систем и CRUD-операции.
"""
import re

from django.db.models import Count

from apps.objects.models import Object
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


class ObjectRepository:
    """Доступ к данным объектов: выборки с фильтрами, сортировкой и счётчиком
    подключённых систем, а также CRUD-операции."""
    ORDERING_FIELDS = {
        "object_name", "hierarchy_level", "status", "city", "created_at", "start_date",
        "category__category_name", "owner_entity__owner_name",
        # Аннотированное поле (Count) — количество подключённых систем.
        "systems_count",
    }
    DEFAULT_ORDERING = ("hierarchy_level", "object_name")

    def get_all(self, level=None, search=None, category=None, system=None,
                owner_entity=None, ordering=None):
        """Возвращает объекты с учётом фильтров, сортировки и счётчика систем.

        Фильтр по юр. лицу иерархический — включает объекты дочерних юр. лиц.
        Поиск через iregex, т.к. на SQLite icontains не игнорирует регистр
        для кириллицы.
        """
        qs = Object.objects.all().select_related("parent_object", "category", "owner_entity")
        if level is not None:
            qs = qs.filter(hierarchy_level=level)
        if search:
            # iregex вместо icontains: на SQLite icontains не игнорирует
            # регистр для не-ASCII символов (кириллицы)
            qs = qs.filter(object_name__iregex=re.escape(search))
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
        # Количество разных подключённых систем (для списков/карточек)
        qs = qs.annotate(systems_count=Count("objectsystem__system", distinct=True))
        return apply_ordering(qs, ordering, self.ORDERING_FIELDS, self.DEFAULT_ORDERING)

    def get_by_id(self, pk):
        """Возвращает объект по id с подгруженными связями и детьми (или None)."""
        return (
            Object.objects.filter(pk=pk)
            .select_related("parent_object", "category", "owner_entity", "creator")
            .prefetch_related("children")
            .first()
        )

    def get_by_creator(self, user, search=None):
        """Возвращает объекты, созданные пользователем (с опциональным поиском)."""
        qs = Object.objects.filter(creator=user).select_related("parent_object", "category", "owner_entity")
        if search:
            qs = qs.filter(object_name__iregex=re.escape(search))
        return qs

    def create(self, **kwargs):
        """Создаёт и возвращает новый объект."""
        return Object.objects.create(**kwargs)

    def update(self, instance, **kwargs):
        """Обновляет переданные поля объекта и сохраняет его."""
        for key, value in kwargs.items():
            setattr(instance, key, value)
        instance.save()
        return instance

    def delete(self, instance):
        """Удаляет объект из БД."""
        instance.delete()
        return instance
