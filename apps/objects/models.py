from django.db import models
from django.contrib.auth.models import User

from apps.system.models import AutomatedSystem
from apps.owners.models import OwnerEntity
from apps.participants.models import Participant


class Object(models.Model):
    LEVEL_CHOICES = [
        (1, "Level 1"),
        (2, "Level 2"),
        (3, "Level 3"),
    ]

    name = models.CharField(max_length=255)
    level = models.PositiveSmallIntegerField(choices=LEVEL_CHOICES)
    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="children",
        limit_choices_to={"is_deleted": False},
    )
    category = models.ForeignKey(
        "categories.Category",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="category_objects",
    )
    owner_entity = models.ForeignKey(
        OwnerEntity,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="owned_objects",
        verbose_name="Юридическое лицо",
    )
    is_deleted = models.BooleanField(default=False)
    creator_id = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["level", "name"]
        verbose_name = "Объект производства"
        verbose_name_plural = "Объекты производства"
    def __str__(self):
        return f"{self.name} (L{self.level})"


class ObjectSystem(models.Model):
    STATUS_CHOICES = [
        ('planned', 'Планируется'),
        ('active', 'В эксплуатации'),
        ('maintenance', 'Обслуживание'),
        ('decommissioned', 'Выведена из эксплуатации'),
    ]

    object = models.ForeignKey(Object, on_delete=models.CASCADE, verbose_name="Объект")
    system = models.ForeignKey(AutomatedSystem, on_delete=models.CASCADE, verbose_name="Система")

    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default='planned',
        verbose_name="Статус"
    )
    implementation_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Дата ввода в эксплуатацию"
    )
    integrator = models.ForeignKey(
        Participant,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="integrated_object_systems",
        verbose_name="Интегратор",
    )
    implimentor = models.ForeignKey(
        Participant,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="implemented_object_systems",
        verbose_name="Исполнитель внедрения",
    )

    class Meta:
        verbose_name = "Система на объекте"
        verbose_name_plural = "Системы на объектах"
        unique_together = ('object', 'system')

    def __str__(self):
        return f"{self.object.name} -> {self.system.autosystem_name}"
