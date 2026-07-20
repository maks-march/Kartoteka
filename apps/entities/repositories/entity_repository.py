"""Репозиторий доступа к данным участников рынка."""
import re

from django.db.models import Count

from apps.entities.models import Entity
from common.ordering import apply_ordering


class EntityRepository:
    """Доступ к данным участников рынка."""
    ORDERING_FIELDS = {
        "entity_name", "inn", "entity_type", "registration_date",
        "is_partner", "systems_count", "products_count",
    }
    DEFAULT_ORDERING = "entity_name"

    @staticmethod
    def _annotate(qs):
        """Добавляет счётчики продуктов и связанных систем (как в сводке).

        products_count — свои вендорские продукты + поставляемые (для ФПЦ —
        сумма; для вендора — только вендорские; для поставщика — только
        поставляемые).

        systems_count — внедрённые системы (число связей ObjectSystem, где
        участник является исполнителем) + вендорские системы (число систем,
        построенных на продуктах участника-вендора) + поставленные системы
        (число связей ObjectSystem, где участник — поставщик). Считаем связи,
        а не различные системы: одна система на нескольких объектах — это
        несколько внедрений/поставок (совпадает со сводкой).
        """
        return qs.annotate(
            products_count=(
                Count("vendor_profile__products", distinct=True)
                + Count("supplier_profile__products", distinct=True)
            ),
            systems_count=(
                # Внедрения: связи ObjectSystem, где участник — исполнитель.
                Count("implemented_object_systems", distinct=True)
                # Вендорские системы: системы на продуктах этого вендора.
                + Count("vendor_profile__products__systems", distinct=True)
                # Поставленные системы: связи, где участник — поставщик.
                + Count("supplied_object_systems", distinct=True)
            ),
        )

    def get_all(self, search=None, ordering=None):
        """Возвращает участников с фильтром/сортировкой и счётчиками продуктов/систем."""
        qs = Entity.objects.all()
        if search:
            # iregex вместо icontains: на SQLite icontains не игнорирует
            # регистр для не-ASCII символов (кириллицы)
            qs = qs.filter(entity_name__iregex=re.escape(search))
        qs = self._annotate(qs)
        return apply_ordering(qs, ordering, self.ORDERING_FIELDS, self.DEFAULT_ORDERING)

    def get_by_id(self, pk):
        """Возвращает участника по id с подгруженными профилями (или None)."""
        return self._annotate(Entity.objects.filter(pk=pk)).first()

    def create(self, **kwargs):
        """Создаёт и возвращает нового участника."""
        return Entity.objects.create(**kwargs)

    def update(self, instance, **kwargs):
        """Обновляет переданные поля участника и сохраняет его."""
        for key, value in kwargs.items():
            setattr(instance, key, value)
        instance.save()
        return instance

    def delete(self, instance):
        """Удаляет участника из БД."""
        instance.delete()
        return instance
