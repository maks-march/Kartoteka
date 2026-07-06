"""Модели автоматизированных систем и классов автоматизации."""
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
        verbose_name="Класс системы (англ. аббревиатура)"
    )
    name_ru = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name="Русская аббревиатура",
        help_text="Русская аббревиатура класса, если есть (напр. РСУ, ПАЗ, ТОИР).",
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="Описание"
    )
    is_composite = models.BooleanField(
        default=False,
        verbose_name="Составной класс",
        help_text="Класс, который может включать подсистемы (MES, MOM, АСУТП и т.п.). "
                  "Для таких систем заполняются «классы подсистем».",
    )
    includes = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="included_by",
        verbose_name="Включает класс",
        help_text="Класс, который автоматически подставляется в подсистемы "
                  "(напр. у MOM здесь MES).",
    )

    class Meta:
        verbose_name = "Класс автоматизации"
        verbose_name_plural = "Классы автоматизации"

    def __str__(self):
        return f"L{self.level} - {self.label}"

    @property
    def label(self):
        """Отображение: «ENG (РУС)», если есть русская аббревиатура, иначе ENG."""
        if self.name_ru:
            return f"{self.system_class} ({self.name_ru})"
        return self.system_class


class VendorProduct(models.Model):
    """Продукт вендора, на котором строится система автоматизации.

    Пока модель содержит название и вендора-владельца (Entity). Остальные поля
    (тип продукта, версия, артикул, класс и т.д.) будут добавлены отдельным
    инкрементом.
    """

    product_name = models.CharField(
        max_length=255,
        verbose_name="Название продукта",
    )
    vendor = models.ForeignKey(
        "entities.Entity",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products",
        verbose_name="Вендор",
    )

    class Meta:
        verbose_name = "Продукт вендора"
        verbose_name_plural = "Продукты вендоров"
        ordering = ["product_name"]

    def __str__(self):
        return self.product_name


class AutomatedSystem(models.Model):

    STATUS_CHOICES = [
        ("active", "В эксплуатации"),
        ("planned", "Планируется"),
        ("unsupported", "Не поддерживается"),
        ("decommissioned", "Выведена из эксплуатации"),
    ]

    STATUS_TAG_CLASSES = {
        "active": "tag-ok",
        "implementing": "tag-warn",
        "planned": "tag-blue",
        "pilot": "tag-blue",
        "unsupported": "tag-danger",
        "decommissioned": "tag-muted",
    }

    autosystem_name = models.CharField(
        max_length=255,
        verbose_name="Полное название системы автоматизации"
    )
    autosystem_short_name = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name="Короткое название системы автоматизации"
    )
    system_class = models.ForeignKey(
        AutomationClass,
        on_delete=models.PROTECT,
        related_name='systems',
        verbose_name="Класс системы"
    )
    subsystem_classes = models.ManyToManyField(
        AutomationClass,
        blank=True,
        related_name="subsystem_of_systems",
        verbose_name="Классы подсистем",
        help_text="Заполняется только для составных классов (MES, MOM, АСУТП): "
                  "какие классы входят в систему.",
    )
    product = models.ForeignKey(
        VendorProduct,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="systems",
        verbose_name="Продукт",
    )

    # --- Состояние продукта ---
    system_status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default="active",
        verbose_name="Статус системы",
    )

    notes = models.TextField(
        blank=True,
        default="",
        verbose_name="Дополнительная информация",
    )

    # --- Жизненный цикл ---
    release_year = models.DateField(
        null=True,
        blank=True,
        verbose_name="Дата выпуска",
    )

    # --- Технические данные ---
    technical_specs = models.JSONField(
        blank=True,
        null=True,
        verbose_name="Технические характеристики",
    )
    modules = models.JSONField(
        blank=True,
        null=True,
        verbose_name="Модули системы",
    )
    interfaces = models.JSONField(
        blank=True,
        null=True,
        verbose_name="Интерфейсы системы",
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

    @property
    def status_tag_class(self):
        return self.STATUS_TAG_CLASSES.get(self.system_status, "tag-muted")

    @staticmethod
    def _json_to_text(value):
        if value in (None, ""):
            return ""
        import json
        return json.dumps(value, ensure_ascii=False, indent=2)

    @property
    def technical_specs_json(self):
        return self._json_to_text(self.technical_specs)

    @property
    def modules_json(self):
        return self._json_to_text(self.modules)

    @property
    def interfaces_json(self):
        return self._json_to_text(self.interfaces)

    @staticmethod
    def _list_to_text(value):
        """Список -> строка через запятую (для предзаполнения текстового поля)."""
        if not value:
            return ""
        if isinstance(value, (list, tuple)):
            return ", ".join(str(v) for v in value)
        return str(value)

    @property
    def modules_text(self):
        return self._list_to_text(self.modules)

    @property
    def interfaces_text(self):
        return self._list_to_text(self.interfaces)

    @property
    def specs_items(self):
        """Пары (ключ, значение) технических характеристик для рендера в форме."""
        if isinstance(self.technical_specs, dict):
            return list(self.technical_specs.items())
        return []
