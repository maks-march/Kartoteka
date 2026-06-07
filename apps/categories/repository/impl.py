"""Django ORM-реализация репозитория категорий."""

from typing import Optional, List

from core.models import Category  # модель из предыдущего шага

from categories.domain.entities import CategoryEntity
from categories.repository.protocol import CategoryRepository
from common.exceptions import NotFoundException


def _to_entity(category: Category) -> CategoryEntity:
    return CategoryEntity(
        id=category.pk,
        name=category.name,
        level=category.level,
    )


class DjangoCategoryRepository(CategoryRepository):

    def create(self, category: CategoryEntity) -> CategoryEntity:
        db_category = Category.objects.create(
            name=category.name,
            level=category.level,
        )
        return _to_entity(db_category)

    def get_by_id(self, category_id: int) -> Optional[CategoryEntity]:
        db_category = Category.objects.filter(pk=category_id).first()
        return _to_entity(db_category) if db_category else None

    def get_all(self, level: Optional[int] = None) -> List[CategoryEntity]:
        qs = Category.objects.all()
        if level is not None:
            qs = qs.filter(level=level)
        qs = qs.order_by("name")
        return [_to_entity(c) for c in qs]

    def update(self, category: CategoryEntity) -> CategoryEntity:
        db_category = Category.objects.filter(pk=category.id).first()
        if not db_category:
            raise NotFoundException(
                message="Категория не найдена",
                details=f"id={category.id}",
            )
        db_category.name = category.name
        db_category.level = category.level
        db_category.save(update_fields=["name", "level"])
        return _to_entity(db_category)

    def delete(self, category_id: int) -> None:
        deleted, _ = Category.objects.filter(pk=category_id).delete()
        if deleted == 0:
            raise NotFoundException(
                message="Категория не найдена",
                details=f"id={category_id}",
            )

    def count_objects(self, category_id: int) -> int:
        category = Category.objects.filter(pk=category_id).first()
        if not category:
            raise NotFoundException(
                message="Категория не найдена",
                details=f"id={category_id}",
            )
        return category.category_objects.count()
