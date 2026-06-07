"""Repository-интерфейс для категорий."""

from abc import ABC, abstractmethod
from typing import Optional, List

from categories.domain.entities import CategoryEntity


class CategoryRepository(ABC):
    """
    Контракт репозитория категорий.
    """

    @abstractmethod
    def create(self, category: CategoryEntity) -> CategoryEntity:
        ...

    @abstractmethod
    def get_by_id(self, category_id: int) -> Optional[CategoryEntity]:
        ...

    @abstractmethod
    def get_all(self, level: Optional[int] = None) -> List[CategoryEntity]:
        ...

    @abstractmethod
    def update(self, category: CategoryEntity) -> CategoryEntity:
        ...

    @abstractmethod
    def delete(self, category_id: int) -> None:
        ...

    @abstractmethod
    def count_objects(self, category_id: int) -> int:
        """Вернуть количество объектов в категории."""
        ...
