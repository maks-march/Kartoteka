from django.db import models


class Entity(models.Model):
    """Участник рынка (вендор, интегратор, поставщик и т.д.)."""

    ENTITY_TYPE_CHOICES = [
        ("vendor", "Вендор"),
        ("system_integrator", "Системный интегратор"),
        ("engineering_company", "Инжиниринговая компания"),
        ("full_cycle_vendor", "Вендор полного цикла"),
        ("supplier", "Поставщик"),
    ]

    # Цветовой класс тега для каждого типа участника (совпадает в таблице,
    # карточках и подробной карточке).
    ENTITY_TYPE_TAG_CLASSES = {
        "vendor": "tag-blue",
        "system_integrator": "tag-ok",
        "engineering_company": "tag-warn",
        "full_cycle_vendor": "tag-3",
        "supplier": "tag-muted",
    }

    # Типы, у которых бывают собственные продукты (для счётчика в карточках).
    TYPES_WITH_PRODUCTS = ("vendor", "full_cycle_vendor", "supplier")

    entity_name = models.CharField(
        max_length=255,
        verbose_name="Название участника рынка",
    )
    inn = models.CharField(
        max_length=12,
        unique=True,
        null=True,
        blank=True,
        verbose_name="ИНН",
    )
    contacts = models.JSONField(
        null=True,
        blank=True,
        verbose_name="Контактная информация",
    )
    registration_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Дата регистрации",
    )
    financial_data = models.JSONField(
        null=True,
        blank=True,
        verbose_name="Финансовые показатели",
    )
    entity_type = models.CharField(
        max_length=50,
        choices=ENTITY_TYPE_CHOICES,
        blank=True,
        default="",
        verbose_name="Тип участника",
    )
    is_partner = models.BooleanField(
        default=False,
        verbose_name="Является ли партнёром",
    )
    website = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name="Ссылка на сайт",
    )
    kam_name = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name="Имя КАМ (Key Account Manager)",
    )
    kam_phone = models.CharField(
        max_length=50,
        blank=True,
        default="",
        verbose_name="Телефон КАМ",
    )
    contact_person = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name="Контакт от ЦК ПА",
    )
    contact_phone = models.CharField(
        max_length=50,
        blank=True,
        default="",
        verbose_name="Телефон от ЦК ПА",
    )
    presentation_url = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name="Ссылка на презентацию",
    )
    profile = models.TextField(
        blank=True,
        default="",
        verbose_name="Профиль компании",
    )
    industries = models.JSONField(
        null=True,
        blank=True,
        verbose_name="Отрасли применения",
    )

    class Meta:
        verbose_name = "Участник рынка"
        verbose_name_plural = "Участники рынка"
        ordering = ["entity_name"]

    def __str__(self):
        return self.entity_name

    @property
    def entity_type_tag_class(self):
        """CSS-класс цветного тега для типа участника."""
        return self.ENTITY_TYPE_TAG_CLASSES.get(self.entity_type, "tag-muted")

    @property
    def can_have_products(self):
        """Может ли у участника быть свои продукты (вендор/полн. цикл/поставщик)."""
        return self.entity_type in self.TYPES_WITH_PRODUCTS

    @property
    def industries_first(self):
        """Первая отрасль (для колонки таблицы)."""
        if isinstance(self.industries, (list, tuple)) and self.industries:
            return str(self.industries[0])
        return ""

    @property
    def industries_first_three(self):
        """Первые три отрасли строкой через запятую (для карточки)."""
        if isinstance(self.industries, (list, tuple)) and self.industries:
            return ", ".join(str(v) for v in self.industries[:3])
        return ""

    # --- Вспомогательные свойства для форм/детали ---

    @property
    def industries_text(self):
        """Отрасли списком через запятую (для предзаполнения поля)."""
        if not self.industries:
            return ""
        if isinstance(self.industries, (list, tuple)):
            return ", ".join(str(v) for v in self.industries)
        return str(self.industries)

    @property
    def contacts_items(self):
        """Пары (ключ, значение) контактов для рендера."""
        if isinstance(self.contacts, dict):
            return list(self.contacts.items())
        return []

    @property
    def financial_data_items(self):
        if isinstance(self.financial_data, dict):
            return list(self.financial_data.items())
        return []
