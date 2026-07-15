"""Репозиторий доступа к данным категорий объектов."""
import re

from apps.categories.models import Category
from common.ordering import apply_ordering


class CategoryRepository:
    """Доступ к данным категорий объектов."""
    ORDERING_FIELDS = {"category_name", "object_level"}
    DEFAULT_ORDERING = ("object_level", "category_name")

    def get_all(self, level=None, search=None, ordering=None):
        """Возвращает категории с учётом фильтров по уровню/поиску и сортировки."""
        qs = Category.objects.all()
        if level is not None:
            qs = qs.filter(object_level=level)
        if search:
            # iregex вместо icontains: на SQLite icontains не игнорирует
            # регистр для не-ASCII символов (кириллицы)
            qs = qs.filter(category_name__iregex=re.escape(search))
        return apply_ordering(qs, ordering, self.ORDERING_FIELDS, self.DEFAULT_ORDERING)

    def get_by_id(self, pk):
        """Возвращает категорию по id (или None)."""
        return Category.objects.filter(pk=pk).select_related("creator").first()

    def get_by_creator(self, user, search=None):
        """Возвращает категории, созданные пользователем."""
        qs = Category.objects.filter(creator=user)
        if search:
            qs = qs.filter(category_name__iregex=re.escape(search))
        return qs

    def create(self, **kwargs):
        """Создаёт и возвращает новую категорию."""
        return Category.objects.create(**kwargs)

    def update(self, instance, **kwargs):
        """Обновляет переданные поля категории и сохраняет её."""
        for key, value in kwargs.items():
            setattr(instance, key, value)
        instance.save()
        return instance

    def delete(self, instance):
        """Удаляет категорию из БД."""
        instance.delete()
        return instance
