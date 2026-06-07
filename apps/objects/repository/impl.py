"""Django ORM-реализация репозитория объектов."""

from typing import Optional, List

from core.models import Object as ObjectModel, Category as CategoryModel

from objects_app.domain.entities import ObjectEntity
from objects_app.repository.protocol import ObjectRepository
from common.exceptions import NotFoundException


def _to_entity(obj: ObjectModel) -> ObjectEntity:
    return ObjectEntity(
        id=obj.pk,
        name=obj.name,
        level=obj.level,
        category_id=obj.category_id,
        category_name=obj.category.name,
    )


class DjangoObjectRepository(ObjectRepository):

    def create(self, obj: ObjectEntity) -> ObjectEntity:
        category = CategoryModel.objects.get(pk=obj.category_id)
        db_obj = ObjectModel.objects.create(
            name=obj.name,
            level=obj.level,
            category=category,
        )
        return _to_entity(db_obj)

    def get_by_id(self, obj_id: int) -> Optional[ObjectEntity]:
        db_obj = ObjectModel.objects.select_related("category").filter(pk=obj_id).first()
        return _to_entity(db_obj) if db_obj else None

    def get_all(
        self,
        level: Optional[int] = None,
        category_id: Optional[int] = None,
        search: Optional[str] = None,
    ) -> List[ObjectEntity]:
        qs = ObjectModel.objects.select_related("category").all()

        if level is not None:
            qs = qs.filter(level=level)
        if category_id is not None:
            qs = qs.filter(category_id=category_id)
        if search:
            qs = qs.filter(name__icontains=search)

        qs = qs.order_by("name")
        return [_to_entity(o) for o in qs]

    def update(self, obj: ObjectEntity) -> ObjectEntity:
        db_obj = ObjectModel.objects.select_related("category").filter(pk=obj.id).first()
        if not db_obj:
            raise NotFoundException(
                message="Объект не найден",
                details=f"id={obj.id}",
            )
        db_obj.name = obj.name
        db_obj.level = obj.level
        db_obj.category_id = obj.category_id
        db_obj.save(update_fields=["name", "level", "category_id"])
        return _to_entity(db_obj)

    def delete(self, obj_id: int) -> None:
        deleted, _ = ObjectModel.objects.filter(pk=obj_id).delete()
        if deleted == 0:
            raise NotFoundException(
                message="Объект не найден",
                details=f"id={obj_id}",
            )
