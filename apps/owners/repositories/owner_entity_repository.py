import re

from apps.owners.models import OwnerEntity


class OwnerEntityRepository:
    def get_all(self, search=None):
        qs = OwnerEntity.objects.all().select_related("owner", "ultimate_owner")
        if search:
            # iregex вместо icontains: на SQLite icontains не игнорирует
            # регистр для не-ASCII символов (кириллицы)
            qs = qs.filter(owner_name__iregex=re.escape(search))
        return qs

    def get_by_id(self, pk):
        return (
            OwnerEntity.objects.filter(pk=pk)
            .select_related("owner", "ultimate_owner")
            .prefetch_related("subsidiaries", "owned_objects")
            .first()
        )

    def create(self, **kwargs):
        return OwnerEntity.objects.create(**kwargs)

    def update(self, instance, **kwargs):
        for key, value in kwargs.items():
            setattr(instance, key, value)
        instance.save()
        return instance

    def delete(self, instance):
        instance.delete()
        return instance
