"""Use-case: обновление категории."""

from categories.domain.entities import CategoryEntity
from categories.repository.protocol import CategoryRepository
from common.exceptions import NotFoundException, ValidationError, ConflictError


class UpdateCategoryUseCase:
    def __init__(self, category_repo: CategoryRepository):
        self.category_repo = category_repo

    def execute(self, category_id: int, name: str, level: int) -> CategoryEntity:
        self._validate_input(name, level)

        existing = self.category_repo.get_by_id(category_id)
        if existing is None:
            raise NotFoundException(
                message="Категория не найдена",
                details=f"id={category_id}",
            )

        # Проверяем дубликаты (исключая саму категорию)
        all_categories = self.category_repo.get_all()
        for cat in all_categories:
            if cat.id != category_id and cat.name.lower() == name.lower():
                raise ConflictError(
                    message="Категория с таким именем уже существует",
                    details=f"name={name}",
                )

        entity = CategoryEntity(id=category_id, name=name, level=level)
        return self.category_repo.update(entity)

    @staticmethod
    def _validate_input(name: str, level: int) -> None:
        errors = []
        if not name or len(name.strip()) < 2:
            errors.append("Название должно содержать минимум 2 символа")
        if level not in (1, 2, 3):
            errors.append("Уровень должен быть 1, 2 или 3")
        if errors:
            raise ValidationError(
                message="Ошибка валидации данных",
                details="; ".join(errors),
            )
