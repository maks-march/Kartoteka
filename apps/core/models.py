"""ORM-модели (инфраструктура)."""

from django.db import models


class Category(models.Model):
    """ORM-модель категории."""

    class Meta:
        db_table = "category"
        ordering = ["name"]
        verbose_name = "категория"
        verbose_name_plural = "категории"

    LEVEL_CHOICES = [
        (1, "Уровень 1"),
        (2, "Уровень 2"),
        (3, "Уровень 3"),
    ]

    name = models.CharField("название", max_length=100, unique=True)
    level = models.PositiveSmallIntegerField(
        "уровень",
        choices=LEVEL_CHOICES,
    )

    def __str__(self):
        return f"{self.name} (уровень {self.level})"


class GameLevel(models.IntegerChoices):
    LEVEL_1 = 1, "Уровень 1"
    LEVEL_2 = 2, "Уровень 2"
    LEVEL_3 = 3, "Уровень 3"


class Object(models.Model):
    """ORM-модель объекта."""

    class Meta:
        db_table = "object"
        ordering = ["name"]
        verbose_name = "объект"
        verbose_name_plural = "объекты"

    name = models.CharField("название", max_length=200)
    level = models.PositiveSmallIntegerField(
        "уровень",
        choices=GameLevel.choices,
        db_index=True,
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="category_objects",
        verbose_name="категория",
    )

    def __str__(self):
        return f"{self.name} (уровень {self.get_level_display()})"
