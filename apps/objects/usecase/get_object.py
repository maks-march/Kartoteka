"""Use-case: получение объектов."""

from typing import List, Optional

from objects_app.domain.entities import ObjectEntity
from objects_app.repository.protocol import ObjectRepository
from common.exceptions import NotFoundException


class GetObjectByIdUseCase:
    def __init__(self, object_repo: ObjectRepository):
        self.object_repo = object_repo

    def execute(self, obj_id: int) -> ObjectEntity:
        entity = self.object_repo.get_by_id(obj_id)
        if entity is None:
            raise NotFoundException(
                message="Объект не найден",
                details=f"id={obj_id}",
            )
        return entity


class ListObjectsUseCase:
    def __init__(self, object_repo: ObjectRepository):
        self.object_repo = object_repo

    def execute(
        self,
        level: Optional[int] = None,
        category_id: Optional[int] = None,
        search: Optional[str] = None,
    ) -> List[ObjectEntity]:
        return self.object_repo.get_all(level=level, category_id=category_id, search=search)