"""Use-case: получение категорий."""

from typing import List, Optional

from categories.domain.entities import CategoryEntity
from categories.repository.protocol import CategoryRepository
from common.exceptions import NotFoundException


class GetCategoryByIdUseCase:
    def __init__(self, category_repo: CategoryRepository):
        self.category_repo = category_repo

    def execute(self, category_id: int) -> CategoryEntity:
        entity = self.category_repo.get_by_id(category_id)
        if entity is None:
            raise NotFoundException(
                message="Категория не найдена",
                details=f"id={category_id}",
            )
        return entity


class ListCategoriesUseCase:
    def __init__(self, category_repo: CategoryRepository):
        self.category_repo = category_repo

    def execute(self, level: Optional[int] = None) -> List[CategoryEntity]:
        return self.category_repo.get_all(level=level)


class GetCategoryObjectCountUseCase:
    def __init__(self, category_repo: CategoryRepository):
        self.category_repo = category_repo

    def execute(self, category_id: int) -> int:
        return self.category_repo.count_objects(category_id)
