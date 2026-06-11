from django.db import models
from django.contrib.auth.models import User


class AutomationClass(models.Model):

    LEVEL_CHOICES = [
        (0, 'L0'),
        (1, 'L1'),
        (2, 'L2'),
        (3, 'L3'),
        (4, 'L4'),
    ]

    level = models.IntegerField(
        choices=LEVEL_CHOICES,
        verbose_name="Уровень автоматизации"
    )
    system_class = models.CharField(
        max_length=255,
        verbose_name="Класс системы"
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="Описание"
    )

    class Meta:
        verbose_name = "Класс автоматизации"
        verbose_name_plural = "Классы автоматизации"

    def __str__(self):
        return f"L{self.level} - {self.system_class}"


class AutomatedSystem(models.Model):

    autosystem_name = models.CharField(
        max_length=255,
        verbose_name="Название системы"
    )
    system_class = models.ForeignKey(
        AutomationClass,
        on_delete=models.PROTECT,
        related_name='systems',
        verbose_name="Класс системы"
    )
    creator_id = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Создатель"
    )

    class Meta:
        verbose_name = "Автоматизированная система"
        verbose_name_plural = "Автоматизированные системы"

    def __str__(self):
        return self.autosystem_name
