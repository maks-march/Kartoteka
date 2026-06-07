"""Use-case: удаление категории."""

from categories.repository.protocol import CategoryRepository


class DeleteCategoryUseCase:
    def __init__(self, category_repo: CategoryRepository):
        self.category_repo = category_repo

    def execute(self, category_id: int) -> None:
        self.category_repo.delete(category_id)
