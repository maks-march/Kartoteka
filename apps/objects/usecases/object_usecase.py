"""Сценарии (use cases) работы с объектами производства.

Слой между представлениями/API и репозиторием: применяет доменную
валидацию и правила наследования (адрес, юр. лицо) перед сохранением.
"""
from apps.objects.repositories.object_repository import ObjectRepository
from apps.objects.usecases.validators import ObjectValidator
from rest_framework.exceptions import NotFound


class ObjectUseCase:
    """Сценарии работы с объектами производства: список с фильтрами/сортировкой,
    получение, создание, обновление и удаление с доменной валидацией."""
    def __init__(self, repo=None):
        """Инициализирует use case, позволяя подменить репозиторий (для тестов)."""
        self.repo = repo or ObjectRepository()
        self.validator = ObjectValidator()

    def list(self, level=None, search=None, category=None, system=None,
             owner_entity=None, ordering=None):
        """Возвращает объекты с учётом фильтров и сортировки."""
        return self.repo.get_all(
            level=level,
            search=search,
            category=category,
            system=system,
            owner_entity=owner_entity,
            ordering=ordering,
        )

    def get(self, pk):
        """Возвращает объект по id или бросает NotFound, если его нет."""
        obj = self.repo.get_by_id(pk)
        if not obj:
            raise NotFound("Object not found")
        return obj

    def list_by_user(self, user, search=None):
        """Возвращает объекты, созданные указанным пользователем."""
        return self.repo.get_by_creator(user, search=search)

    # Адресные поля, которые наследуются от родителя (title — исключение, он свой)
    INHERITED_ADDRESS_FIELDS = ("country", "region", "city", "street", "house")

    def get_parent_address_defaults(self, parent_id):
        """Возвращает наследуемые адресные поля родителя для предзаполнения формы."""
        if parent_id in (None, "", "None"):
            return {}
        parent = self.repo.get_by_id(parent_id)
        if not parent:
            return {}
        return {field: getattr(parent, field, "") for field in self.INHERITED_ADDRESS_FIELDS}

    def get_parent_owner_entity_id(self, parent_id):
        """Возвращает id юр. лица (OwnerEntity) родителя.

        Для объектов 2-го и 3-го уровня юр. лицо не выбирается вручную,
        а наследуется от родителя (если родитель есть). Нет родителя — None.
        """
        if parent_id in (None, "", "None"):
            return None
        parent = self.repo.get_by_id(parent_id)
        if not parent:
            return None
        return parent.owner_entity_id

    def create(self, user, **data):
        """Создаёт объект: валидирует связи, наследует адрес и юр. лицо от родителя.

        Для L2/L3 юр. лицо берётся от родителя (значение из формы игнорируется),
        а пустые адресные поля дозаполняются из родителя.
        """
        parent_id = data.pop("parent", None)
        category_id = data.pop("category", None)
        owner_entity_id = data.pop("owner_entity", None)
        level = data.get("hierarchy_level")

        # Юр. лицо (владелец) для L2/L3 наследуется от родителя, а не из формы.
        # У объектов 1-го уровня — выбирается вручную.
        if level in (2, 3, "2", "3"):
            owner_entity_id = self.get_parent_owner_entity_id(parent_id)

        self.validator.validate_parent(parent_id, level)
        self.validator.validate_category(category_id, level)
        self.validator.validate_owner_entity(owner_entity_id)
        self.validator.validate_title(data.get("title"), level)

        # Наследование адреса от родителя: заполняем только те адресные поля,
        # которые не переданы явно (или переданы пустыми). title не наследуется.
        if parent_id is not None:
            defaults = self.get_parent_address_defaults(parent_id)
            for field, value in defaults.items():
                if not data.get(field):
                    data[field] = value

        if parent_id is not None:
            data["parent_object_id"] = parent_id
        if category_id is not None:
            data["category_id"] = category_id
        if owner_entity_id is not None:
            data["owner_entity_id"] = owner_entity_id
        data["creator"] = user
        return self.repo.create(**data)

    def update(self, pk, user, **data):
        """Обновляет объект: валидирует изменённые связи и уровень.

        Обновляются только переданные поля. Для L2/L3 юр. лицо пере-наследуется
        от эффективного родителя (в т.ч. при переносе под другого родителя).
        """
        obj = self.get(pk)
        parent_id = data.pop("parent", "__missing__")
        category_id = data.pop("category", "__missing__")
        owner_entity_id = data.pop("owner_entity", "__missing__")
        level = data.get("hierarchy_level", obj.hierarchy_level)

        if parent_id != "__missing__":
            self.validator.validate_parent(parent_id, level, instance=obj)
            data["parent_object_id"] = parent_id
        if category_id != "__missing__":
            self.validator.validate_category(category_id, level)
            data["category_id"] = category_id

        # Юр. лицо (владелец): для L2/L3 наследуется от родителя (эффективного —
        # с учётом возможной смены родителя), для L1 берётся из формы.
        effective_parent_id = (
            parent_id if parent_id != "__missing__" else obj.parent_object_id
        )
        if level in (2, 3, "2", "3"):
            inherited_owner_id = self.get_parent_owner_entity_id(effective_parent_id)
            self.validator.validate_owner_entity(inherited_owner_id)
            data["owner_entity_id"] = inherited_owner_id
        elif owner_entity_id != "__missing__":
            self.validator.validate_owner_entity(owner_entity_id)
            data["owner_entity_id"] = owner_entity_id

        # Валидация title: уровень определяем по новому значению (если меняется),
        # иначе по текущему уровню объекта.
        if "title" in data:
            effective_level = data.get("hierarchy_level", obj.hierarchy_level)
            self.validator.validate_title(data.get("title"), effective_level)

        if "hierarchy_level" in data and data["hierarchy_level"] != obj.hierarchy_level:
            # При смене уровня перепроверяем текущего родителя и категорию
            current_parent_id = data.get("parent_object_id", obj.parent_object_id)
            if current_parent_id is not None:
                self.validator.validate_parent(current_parent_id, data["hierarchy_level"], instance=obj)
            current_category_id = data.get("category_id", obj.category_id)
            if current_category_id is not None:
                self.validator.validate_category(current_category_id, data["hierarchy_level"])

        return self.repo.update(obj, **data)

    def delete(self, pk, user):
        """Удаляет объект по id."""
        obj = self.get(pk)
        return self.repo.delete(obj)
