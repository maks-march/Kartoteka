from django.core.exceptions import ValidationError

from apps.objects.models import Object
from apps.categories.models import Category


class ObjectValidator:
    def validate_parent(self, parent_id, level, instance=None):
        if parent_id is None:
            return

        if level == 1:
            raise ValidationError("Объект первого уровня не может иметь родителя")

        try:
            parent = Object.objects.get(pk=parent_id, is_deleted=False)
        except Object.DoesNotExist:
            raise ValidationError("Родительский объект не найден")

        if parent.level >= level:
            raise ValidationError(
                "Уровень родительского объекта должен быть ниже уровня дочернего объекта"
            )

        if instance and parent.pk == instance.pk:
            raise ValidationError("Объект не может быть родителем самому себе")

        if instance:
            current = parent
            while current.parent:
                if current.parent.pk == instance.pk:
                    raise ValidationError(
                        "Обнаружен цикл: нельзя назначить потомка родителем"
                    )
                current = current.parent

    def validate_category(self, category_id, object_level):
        if category_id is None:
            return

        try:
            category = Category.objects.get(pk=category_id)
        except Category.DoesNotExist:
            raise ValidationError("Категория не найдена")

        if category.level != object_level:
            raise ValidationError(
                "Уровень категории должен совпадать с уровнем объекта"
            )