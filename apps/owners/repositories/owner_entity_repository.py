import re

from apps.owners.models import OwnerEntity
from common.ordering import apply_ordering


class OwnerEntityRepository:
    """Доступ к данным юридических лиц, включая обход дерева владения."""
    ORDERING_FIELDS = {"owner_name", "is_root"}
    DEFAULT_ORDERING = "owner_name"

    def get_all(self, search=None, ordering=None, roots_only=False):
        qs = OwnerEntity.objects.all().select_related("owner", "ultimate_owner")
        if roots_only:
            qs = qs.filter(is_root=True)
        if search:
            # iregex вместо icontains: на SQLite icontains не игнорирует
            # регистр для не-ASCII символов (кириллицы)
            qs = qs.filter(owner_name__iregex=re.escape(search))
        return apply_ordering(qs, ordering, self.ORDERING_FIELDS, self.DEFAULT_ORDERING)

    def get_roots(self, ordering=None):
        """Материнские компании (верхний уровень иерархии)."""
        return self.get_all(ordering=ordering, roots_only=True)

    def get_by_id(self, pk):
        return (
            OwnerEntity.objects.filter(pk=pk)
            .select_related("owner", "ultimate_owner")
            .prefetch_related("subsidiaries", "owned_objects")
            .first()
        )

    def get_descendant_ids(self, ids):
        """Возвращает id переданных юр. лиц вместе со всеми их потомками.

        Потомок — это юр. лицо, у которого поле ``owner`` (ближайший владелец)
        прямо или транзитивно указывает на одного из переданных id.
        Обход выполняется вниз по дереву ``subsidiaries`` с защитой от циклов.
        """
        seen = set()
        frontier = {int(i) for i in ids if i not in (None, "", "None")}

        while frontier:
            seen |= frontier
            children = OwnerEntity.objects.filter(owner_id__in=frontier).values_list(
                "id", flat=True
            )
            # В следующую волну берём только ещё не обойдённых (защита от циклов).
            frontier = set(children) - seen

        return seen

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
