"""Модели объектов производства и связи «система на объекте»."""
from django.db import models
from django.contrib.auth.models import User

from apps.system.models import AutomationSystem
from apps.owners.models import OwnerEntity
from apps.entities.models import Entity


class Object(models.Model):
    """Объект производства: завод, цех или установка.

    Образует трёхуровневую иерархию (self-ссылка ``parent_object``):
    производство (L1) → цех (L2) → установка (L3). Хранит названия, адрес,
    характеристики, категорию и юридическое лицо-владельца.
    """

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

    object_name = models.CharField(max_length=255, verbose_name="Полное название объекта")
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
    hierarchy_level = models.PositiveSmallIntegerField(choices=LEVEL_CHOICES)
    parent_object = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="children",
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
        verbose_name="Титульный номер",
        help_text="Титульный номер объекта (уровни 2 и 3)",
    )

    creator = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Мета-настройки: сортировка и человекочитаемые имена."""

        ordering = ["hierarchy_level", "object_name"]
        verbose_name = "Объект производства"
        verbose_name_plural = "Объекты производства"
    def __str__(self):
        """Строковое представление: название и уровень иерархии."""
        return f"{self.object_name} (L{self.hierarchy_level})"

    @property
    def address_line(self):
        """Адрес одной строкой через запятую (без пустых частей).

        title (титульный номер, уровни 2 и 3) добавляется в конце, если задан.
        """
        parts = [self.country, self.region, self.city, self.street, self.house]
        line = ", ".join(p.strip() for p in parts if p and p.strip())
        if self.hierarchy_level in (2, 3) and self.title and self.title.strip():
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
        """CSS-класс тега для текущего статуса (для единообразия в шаблонах)."""
        return self.STATUS_TAG_CLASSES.get(self.status, "tag-muted")


class ObjectSystem(models.Model):
    """Связь «система на объекте»: какая AutomationSystem внедрена на Object.

    Хранит статус внедрения, дату ввода и компанию-исполнителя. Пара
    (объект, система) уникальна.
    """

    STATUS_CHOICES = [
        ('planned', 'Планируется'),
        ('active', 'В эксплуатации'),
        ('maintenance', 'Обслуживание'),
        ('decommissioned', 'Не эксплуатируется'),
    ]

    object = models.ForeignKey(Object, on_delete=models.CASCADE, verbose_name="Объект")
    system = models.ForeignKey(AutomationSystem, on_delete=models.CASCADE, verbose_name="Система")

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
    implementor = models.ForeignKey(
        Entity,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="implemented_object_systems",
        verbose_name="Исполнитель внедрения",
    )

    class Meta:
        """Мета-настройки: имена и уникальность пары (объект, система)."""

        verbose_name = "Система на объекте"
        verbose_name_plural = "Системы на объектах"
        unique_together = ('object', 'system')

    def __str__(self):
        """Строковое представление: «объект → система»."""
        return f"{self.object.object_name} -> {self.system.autosystem_name}"

    # Соответствие статуса внедрения css-классу тега (единый цвет со сводкой).
    STATUS_TAG_CLASSES = {
        "active": "tag-ok",
        "planned": "tag-blue",
        "maintenance": "tag-warn",
        "decommissioned": "tag-danger",
    }

    @property
    def status_tag_class(self):
        """CSS-класс тега для текущего статуса внедрения системы."""
        return self.STATUS_TAG_CLASSES.get(self.status, "tag-muted")
