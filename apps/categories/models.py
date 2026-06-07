from django.db import models


class Category(models.Model):
    LEVEL_CHOICES = [
        (1, "Level 1"),
        (2, "Level 2"),
        (3, "Level 3"),
    ]

    name = models.CharField(max_length=255)
    level = models.PositiveSmallIntegerField(choices=LEVEL_CHOICES)

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        ordering = ["level", "name"]

    def __str__(self):
        return f"{self.name} (L{self.level})"
