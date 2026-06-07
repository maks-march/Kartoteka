from django.core.exceptions import ValidationError

from apps.objects.models import Object


class ObjectValidator:
    def validate_parent(self, parent_id, level, instance=None):
        if parent_id is None:
            return

        if level == 1:
            raise ValidationError("У первого уровня не может быть родителя")

        try:
            parent = Object.objects.get(pk=parent_id, is_deleted=False)
        except Object.DoesNotExist:
            raise ValidationError("Родитель не найден")

        if parent.level >= level:
            raise ValidationError(
                "Родитель должен быть на уровень меньше"
            )

        if instance and parent.pk == instance.pk:
            raise ValidationError("An object cannot be its own parent")

        if instance:
            current = parent
            while current.parent:
                if current.parent.pk == instance.pk:
                    raise ValidationError(
                        "Cycle detected: cannot set a descendant as parent"
                    )
                current = current.parent
