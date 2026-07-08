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

    # Типы, у которых заводится профиль вендора (точка привязки продуктов).
    VENDOR_TYPES = ("vendor", "full_cycle_vendor")

    @property
    def can_have_products(self):
        """Может ли у участника быть свои продукты (вендор/полн. цикл/поставщик)."""
        return self.entity_type in self.TYPES_WITH_PRODUCTS

    @property
    def is_vendor_type(self):
        """Тип, для которого заводится VendorProfile (vendor / full_cycle_vendor)."""
        return self.entity_type in self.VENDOR_TYPES

    @property
    def is_engineering_type(self):
        return self.entity_type == "engineering_company"

    @property
    def products(self):
        """Продукты вендора (через VendorProfile). Пусто, если профиля нет."""
        from apps.system.models import VendorProduct
        profile = getattr(self, "vendor_profile", None)
        if profile is None:
            return VendorProduct.objects.none()
        return profile.products.all()

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


class VendorProfile(models.Model):
    """Профиль вендора (типы vendor / full_cycle_vendor).

    Почти пустой по собственным полям, но служит точкой привязки продуктов:
    VendorProduct.vendor ссылается именно на VendorProfile, что гарантирует
    «продукт может принадлежать только вендору / вендору полного цикла».
    """

    entity = models.OneToOneField(
        Entity,
        on_delete=models.CASCADE,
        related_name="vendor_profile",
        verbose_name="Участник",
    )

    class Meta:
        verbose_name = "Профиль вендора"
        verbose_name_plural = "Профили вендоров"

    def __str__(self):
        return f"VendorProfile: {self.entity.entity_name}"

    @property
    def entity_name(self):
        """Имя участника — для удобного доступа из шаблонов (product.vendor.entity_name)."""
        return self.entity.entity_name


class EngineeringCompanyProfile(models.Model):
    """Профиль инжиниринговой компании (тип engineering_company)."""

    entity = models.OneToOneField(
        Entity,
        on_delete=models.CASCADE,
        related_name="engineering_profile",
        verbose_name="Участник",
    )
    region = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name="Локация (регион)",
        help_text="Регион деятельности. Подсказки — регионы существующих объектов.",
    )
    resident_object = models.ForeignKey(
        "objects.Object",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="resident_engineering_companies",
        verbose_name="Вхожий объект",
        help_text="Объект, на котором компания уже закрепилась и работает.",
    )
    product_competencies = models.ManyToManyField(
        "system.VendorProduct",
        blank=True,
        related_name="competent_engineering_companies",
        verbose_name="Узкая компетенция по продуктам",
    )

    class Meta:
        verbose_name = "Профиль инжиниринговой компании"
        verbose_name_plural = "Профили инжиниринговых компаний"

    def __str__(self):
        return f"EngineeringCompanyProfile: {self.entity.entity_name}"


class FunctionCompetency(models.Model):
    """Узкая компетенция инж. компании по функции: пара «класс + индустрия».

    Каждая строка — одна связанная пара (напр. MES · Нефтехимия).
    """

    profile = models.ForeignKey(
        EngineeringCompanyProfile,
        on_delete=models.CASCADE,
        related_name="function_competencies",
        verbose_name="Профиль инжиниринговой компании",
    )
    system_class = models.ForeignKey(
        "system.AutomationClass",
        on_delete=models.CASCADE,
        related_name="function_competencies",
        verbose_name="Класс систем",
    )
    industry = models.CharField(
        max_length=255,
        verbose_name="Индустрия",
        help_text="Значение из категорий 1-го уровня (без жёсткой связи).",
    )

    class Meta:
        verbose_name = "Компетенция по функции"
        verbose_name_plural = "Компетенции по функции"
        ordering = ["system_class__level", "system_class__system_class", "industry"]

    def __str__(self):
        return f"{self.system_class.system_class} · {self.industry}"
