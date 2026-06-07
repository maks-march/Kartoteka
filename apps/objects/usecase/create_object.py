"""Use-case: создание объекта."""

from objects_app.domain.entities import ObjectEntity
from objects_app.repository.protocol import ObjectRepository
from common.exceptions import ValidationError
from categories.repository.protocol import CategoryRepository
from common.exceptions import NotFoundException


class CreateObjectUseCase:
    def __init__(self, object_repo: ObjectRepository, category_repo: CategoryRepository):
        self.object_repo = object_repo
        self.category_repo = category_repo

    def execute(self, name: str, level: int, category_id: int) -> ObjectEntity:
        self._validate_input(name, level, category_id)

        # Проверяем, что категория существует
        category = self.category_repo.get_by_id(category_id)
        if category is None:
            raise NotFoundException(
                message="Категория не найдена",
                details=f"id={category_id}",
            )

        entity = ObjectEntity(name=name, level=level, category_id=category_id)
        return self.object_repo.create(entity)

    @staticmethod
    def _validate_input(name: str, level: int, category_id: int) -> None:
        errors = []
        if not name or len(name.strip()) < 2:
            errors.append("Название должно содержать минимум 2 символа")
        if level not in (1, 2, 3):
            errors.append("Уровень должен быть 1, 2 или 3")
        if not category_id:
            errors.append("Необходимо указать категорию")
        if errors:
            raise ValidationError(
                message="Ошибка валидации данных",
                details="; ".join(errors),
            )
