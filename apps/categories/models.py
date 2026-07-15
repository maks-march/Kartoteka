"""Модель категорий объектов производства."""
from django.db import models
from django.contrib.auth.models import User


class Category(models.Model):
    """Категория объекта, привязанная к уровню иерархии (1–3)."""
    LEVEL_CHOICES = [
        (1, "Level 1"),
        (2, "Level 2"),
        (3, "Level 3"),
    ]

    category_name = models.CharField(max_length=255)
    object_level = models.PositiveSmallIntegerField(choices=LEVEL_CHOICES)
    creator = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        """Мета-настройки: имена и сортировка."""
        verbose_name = "Категория объекта"
        verbose_name_plural = "Категории"
        ordering = ["object_level", "category_name"]

    def __str__(self):
        """Строковое представление: название и уровень."""
        return f"{self.category_name} (L{self.object_level})"
