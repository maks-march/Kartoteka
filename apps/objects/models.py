"""Модели объектов производства и связи «система на объекте»."""
from django.db import models
from django.contrib.auth.models import User

from apps.system.models import AutomatedSystem
from apps.owners.models import OwnerEntity
from apps.entities.models import Entity


class Object(models.Model):
    LEVEL_CHOICES = [
        (1, "Level 1"),
        (2, "Level 2"),
        (3, "Level 3"),
    ]

    STATUS_CHOICES = [
        ("active", "В эксплуатации"),
        ("in_project", "В проекте"),
        ("reconstruction", "Реконструкция"),
        ("stopped", "Остановлен"),
    ]

    name = models.CharField(max_length=255, verbose_name="Полное название объекта")
    object_short_name = models.CharField(
        max_length=255, blank=True, default="", verbose_name="Короткое название объекта"
    )
    object_old_name = models.CharField(
        max_length=255, blank=True, default="", verbose_name="Историческое название объекта"
    )
    object_law_name = models.CharField(
        max_length=255, blank=True, default="", verbose_name="Юридическое название объекта"
    )
    object_class = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name="Классификация объекта",
        help_text="Завод, цех, очередь, установка",
    )
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

    # --- Характеристики ---
    start_date = models.DateField(
        null=True, blank=True, verbose_name="Дата ввода в эксплуатацию"
    )
    is_reconstructed = models.BooleanField(
        default=False, verbose_name="Была реконструкция"
    )
    capacity = models.CharField(
        max_length=255, blank=True, default="", verbose_name="Мощность / объём производства"
    )
    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default="active",
        verbose_name="Состояние объекта",
    )
    notes = models.TextField(blank=True, default="", verbose_name="Дополнительная информация")

    # --- Адрес (поля прямо в объекте) ---
    country = models.CharField(max_length=255, blank=True, default="", verbose_name="Страна")
    region = models.CharField(max_length=255, blank=True, default="", verbose_name="Регион")
    city = models.CharField(max_length=255, blank=True, default="", verbose_name="Город")
    street = models.CharField(max_length=255, blank=True, default="", verbose_name="Улица")
    house = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name="Дом",
        help_text="Адрес производства (уровень 1)",
    )
    title = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name="Кодовое расположение",
        help_text="Адрес/расположение установки внутри цеха (только уровень 3)",
    )
    fias_code = models.CharField(
        max_length=255, blank=True, default="", verbose_name="Код ФИАС"
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

    @property
    def address_line(self):
        """Адрес одной строкой через запятую (без пустых частей).

        title (кодовое расположение установки, только уровень 3) добавляется
        в конце, если задан.
        """
        parts = [self.country, self.region, self.city, self.street, self.house]
        line = ", ".join(p.strip() for p in parts if p and p.strip())
        if self.level == 3 and self.title and self.title.strip():
            extra = self.title.strip()
            line = f"{line}, {extra}" if line else extra
        return line

    # Соответствие статуса объекта css-классу тега (для единообразия в шаблонах).
    STATUS_TAG_CLASSES = {
        "active": "tag-ok",
        "in_project": "tag-blue",
        "reconstruction": "tag-warn",
        "stopped": "tag-danger",
    }

    @property
    def status_tag_class(self):
        return self.STATUS_TAG_CLASSES.get(self.status, "tag-muted")


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
        Entity,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="integrated_object_systems",
        verbose_name="Интегратор",
    )
    implimentor = models.ForeignKey(
        Entity,
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
