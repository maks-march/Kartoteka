"""Repository-интерфейс для объектов."""

from abc import ABC, abstractmethod
from typing import Optional, List

from objects_app.domain.entities import ObjectEntity


class ObjectRepository(ABC):
    """
    Контракт репозитория объектов.
    """

    @abstractmethod
    def create(self, obj: ObjectEntity) -> ObjectEntity:
        ...

    @abstractmethod
    def get_by_id(self, obj_id: int) -> Optional[ObjectEntity]:
        ...

    @abstractmethod
    def get_all(
        self,
        level: Optional[int] = None,
        category_id: Optional[int] = None,
        search: Optional[str] = None,
    ) -> List[ObjectEntity]:
        ...

    @abstractmethod
    def update(self, obj: ObjectEntity) -> ObjectEntity:
        ...

    @abstractmethod
    def delete(self, obj_id: int) -> None:
        ...
