"""Use-case: создание категории."""

from categories.domain.entities import CategoryEntity
from categories.repository.protocol import CategoryRepository
from common.exceptions import ValidationError, ConflictError


class CreateCategoryUseCase:
    def __init__(self, category_repo: CategoryRepository):
        self.category_repo = category_repo

    def execute(self, name: str, level: int) -> CategoryEntity:
        self._validate_input(name, level)

        # Проверяем дубликаты
        existing = self.category_repo.get_all()
        if any(c.name.lower() == name.lower() for c in existing):
            raise ConflictError(
                message="Категория с таким именем уже существует",
                details=f"name={name}",
            )

        entity = CategoryEntity(name=name, level=level)
        return self.category_repo.create(entity)

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
