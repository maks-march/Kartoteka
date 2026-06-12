import re

from apps.objects.models import Object


class ObjectRepository:
    def get_all(self, level=None, search=None, category=None, system=None):
        qs = Object.objects.filter(is_deleted=False).select_related("parent", "category")
        if level is not None:
            qs = qs.filter(level=level)
        if search:
            # iregex вместо icontains: на SQLite icontains не игнорирует
            # регистр для не-ASCII символов (кириллицы)
            qs = qs.filter(name__iregex=re.escape(search))
        if category is not None:
            qs = qs.filter(category_id=category)
        if system is not None:
            # только объекты, к которым привязана указанная система
            qs = qs.filter(objectsystem__system_id=system)
        return qs

    def get_by_id(self, pk):
        return (
            Object.objects.filter(pk=pk, is_deleted=False)
            .select_related("parent", "category", "creator_id")
            .prefetch_related("children")
            .first()
        )

    def get_by_creator(self, user, search=None):
        qs = Object.objects.filter(is_deleted=False, creator_id=user).select_related("parent", "category")
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
