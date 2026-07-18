"""Модели участников рынка (Entity) и их типовых профилей."""
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

    class Meta:
        """Мета-настройки модели."""
        verbose_name = "Участник рынка"
        verbose_name_plural = "Участники рынка"
        ordering = ["entity_name"]

    def __str__(self):
        """Строковое представление объекта."""
        return self.entity_name

    @property
    def entity_type_tag_class(self):
        """CSS-класс цветного тега для типа участника."""
        return self.ENTITY_TYPE_TAG_CLASSES.get(self.entity_type, "tag-muted")

    # Типы, у которых заводится профиль вендора (точка привязки продуктов).
    VENDOR_TYPES = ("vendor", "full_cycle_vendor")
    # Типы с профилем поставщика (множественная связь с продуктами).
    SUPPLIER_TYPES = ("supplier", "full_cycle_vendor")
    # Типы с профилем инжиниринговой компании (регион/объект/компетенции).
    ENGINEERING_TYPES = ("engineering_company", "full_cycle_vendor")

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
        """Тип с профилем инж. компании (engineering_company / full_cycle_vendor)."""
        return self.entity_type in self.ENGINEERING_TYPES

    @property
    def is_supplier_type(self):
        """Тип с профилем поставщика (supplier / full_cycle_vendor)."""
        return self.entity_type in self.SUPPLIER_TYPES

    @property
    def is_system_integrator_type(self):
        """Тип, для которого заводится SystemIntegratorProfile."""
        return self.entity_type == "system_integrator"

    @property
    def products(self):
        """Продукты вендора (через VendorProfile). Пусто, если профиля нет."""
        from apps.system.models import VendorProduct
        profile = getattr(self, "vendor_profile", None)
        if profile is None:
            return VendorProduct.objects.none()
        return profile.products.all()

    @property
    def industries(self):
        """Отрасли участника — вычисляются из связей по типу (не хранятся).

        Источники по типу:
        - вендор: отрасли своих продуктов;
        - поставщик: отрасли поставляемых продуктов;
        - инжиниринговая компания: отрасли из компетенций по функции +
          отрасли продуктов, являющихся компетенцией;
        - вендор полного цикла: объединение вышеперечисленного.

        Системный интегратор здесь не обрабатывается (его компетенции
        задаются «от обратного» — будет реализовано отдельно).

        Возвращает queryset уникальных категорий 1-го уровня (Category).
        """
        from apps.categories.models import Category

        ids = set()

        # Вендор / полный цикл: отрасли собственных продуктов (через VendorProfile).
        if self.is_vendor_type:
            vp = getattr(self, "vendor_profile", None)
            if vp is not None:
                ids |= set(
                    Category.objects.filter(industry_products__vendor=vp)
                    .values_list("pk", flat=True)
                )

        # Поставщик / полный цикл: отрасли поставляемых продуктов.
        if self.is_supplier_type:
            sp = getattr(self, "supplier_profile", None)
            if sp is not None:
                ids |= set(
                    Category.objects.filter(industry_products__suppliers=sp)
                    .values_list("pk", flat=True)
                )

        # Инжиниринговая компания: компетенции по функции + отрасли
        # продуктов-компетенций.
        if self.is_engineering_type:
            eng = getattr(self, "engineering_profile", None)
            if eng is not None:
                ids |= set(eng.function_competencies.values_list("industry_id", flat=True))
                ids |= set(
                    Category.objects.filter(industry_products__competent_engineering_companies=eng)
                    .values_list("pk", flat=True)
                )

        # Вендор полного цикла: dedicated профиль (компетенции по функции +
        # отрасли устанавливаемых продуктов).
        if self.entity_type == "full_cycle_vendor":
            fc = getattr(self, "full_cycle_profile", None)
            if fc is not None:
                ids |= set(fc.function_competencies.values_list("industry_id", flat=True))
                ids |= set(
                    Category.objects.filter(industry_products__full_cycle_competent_vendors=fc)
                    .values_list("pk", flat=True)
                )

        return Category.objects.filter(pk__in=ids).order_by("category_name")

    @property
    def industries_names(self):
        """Названия вычисленных отраслей участника списком."""
        return [c.category_name for c in self.industries]

    @property
    def industries_first(self):
        """Первая отрасль (для колонки таблицы)."""
        names = self.industries_names
        return names[0] if names else ""

    @property
    def industries_first_three(self):
        """Первые три отрасли строкой через запятую (для карточки)."""
        return ", ".join(self.industries_names[:3])

    # --- Вспомогательные свойства для форм/детали ---

    @property
    def industries_text(self):
        """Отрасли списком через запятую (для отображения)."""
        return ", ".join(self.industries_names)

    @property
    def contacts_items(self):
        """Пары (ключ, значение) контактов для рендера."""
        if isinstance(self.contacts, dict):
            return list(self.contacts.items())
        return []

    @property
    def financial_data_items(self):
        """Финансовые показатели как список пар (ключ, значение) для шаблонов."""
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
        """Мета-настройки модели."""
        verbose_name = "Профиль вендора"
        verbose_name_plural = "Профили вендоров"

    def __str__(self):
        """Строковое представление объекта."""
        return f"VendorProfile: {self.entity.entity_name}"

    @property
    def entity_name(self):
        """Имя участника — для удобного доступа из шаблонов (product.vendor.entity_name)."""
        return self.entity.entity_name


class SupplierProfile(models.Model):
    """Профиль поставщика (тип supplier).

    Поставщик, в отличие от вендора (связь через авторство продукта —
    VendorProduct.vendor), связан с продуктами МНОЖЕСТВЕННОЙ связью со своей
    стороны: один поставщик поставляет много продуктов, один продукт может
    поставляться многими поставщиками (независимо от того, кто его автор-вендор).
    """

    entity = models.OneToOneField(
        Entity,
        on_delete=models.CASCADE,
        related_name="supplier_profile",
        verbose_name="Участник",
    )
    products = models.ManyToManyField(
        "system.VendorProduct",
        blank=True,
        related_name="suppliers",
        verbose_name="Поставляемые продукты",
    )

    class Meta:
        """Мета-настройки модели."""
        verbose_name = "Профиль поставщика"
        verbose_name_plural = "Профили поставщиков"

    def __str__(self):
        """Строковое представление объекта."""
        return f"SupplierProfile: {self.entity.entity_name}"

    @property
    def entity_name(self):
        """Имя участника — для удобного доступа из шаблонов."""
        return self.entity.entity_name


class SystemIntegratorProfile(models.Model):
    """Профиль системного интегратора (тип system_integrator).

    Особенности типа:
    - managing_owner — управляющая компания из OwnerEntity (внутренний
      интегратор холдинга); необязательная.
    - vendor_partners — вендоры-партнёры (M2M к VendorProfile). Обратная связь
      vendor_profile.partner_integrators даёт «карту партнёров» для вендора.
    """

    entity = models.OneToOneField(
        Entity,
        on_delete=models.CASCADE,
        related_name="system_integrator_profile",
        verbose_name="Участник",
    )
    managing_owner = models.ForeignKey(
        "owners.OwnerEntity",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="internal_integrators",
        verbose_name="Управляющая компания",
        help_text="Компания из OwnerEntity, если это внутренний интегратор.",
    )
    vendor_partners = models.ManyToManyField(
        "entities.VendorProfile",
        blank=True,
        related_name="partner_integrators",
        verbose_name="Вендоры-партнёры",
    )

    class Meta:
        """Мета-настройки модели."""
        verbose_name = "Профиль системного интегратора"
        verbose_name_plural = "Профили системных интеграторов"

    def __str__(self):
        """Строковое представление объекта."""
        return f"SystemIntegratorProfile: {self.entity.entity_name}"

    @property
    def entity_name(self):
        """Имя участника — для удобного доступа из шаблонов."""
        return self.entity.entity_name


class SystemIntegratorFunctionCompetency(models.Model):
    """Исключение из компетенций системного интегратора («от обратного»).

    Интегратор по умолчанию работает СО ВСЕМИ отраслями и классами; записи в
    этой таблице — то, с чем он НЕ работает. Обе ссылки nullable:
    - класс без отрасли  → не работает с этим классом во всех отраслях;
    - отрасль без класса → не работает ни с чем в этой отрасли;
    - класс и отрасль    → не работает с этим классом именно в этой отрасли.
    Хотя бы одно поле должно быть заполнено. Нет записей → работает со всеми.
    """

    profile = models.ForeignKey(
        SystemIntegratorProfile,
        on_delete=models.CASCADE,
        related_name="function_competencies",
        verbose_name="Профиль системного интегратора",
    )
    system_class = models.ForeignKey(
        "system.AutomationClass",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="integrator_excluded_competencies",
        verbose_name="Класс систем (исключение)",
        help_text="Пусто — исключение по всем классам (в указанной отрасли).",
    )
    industry = models.ForeignKey(
        "categories.Category",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="integrator_excluded_competencies",
        verbose_name="Индустрия (исключение)",
        help_text="Индустрия — категория 1-го уровня. Пусто — исключение во всех отраслях.",
    )

    class Meta:
        """Мета-настройки модели."""
        verbose_name = "Исключение компетенции интегратора"
        verbose_name_plural = "Исключения компетенций интегратора"
        ordering = ["system_class__level", "system_class__system_class", "industry__category_name"]

    def __str__(self):
        """Строковое представление исключения («класс · индустрия», с «Все»)."""
        cls = self.system_class.system_class if self.system_class else "Все классы"
        ind = self.industry.category_name if self.industry else "Все отрасли"
        return f"кроме: {cls} · {ind}"


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
        """Мета-настройки модели."""
        verbose_name = "Профиль инжиниринговой компании"
        verbose_name_plural = "Профили инжиниринговых компаний"

    def __str__(self):
        """Строковое представление объекта."""
        return f"EngineeringCompanyProfile: {self.entity.entity_name}"


class EngineeringCompanyFunctionCompetency(models.Model):
    """Узкая компетенция инж. компании по функции: пара «класс + индустрия».

    Смысл прямой — компания РАБОТАЕТ с этим сочетанием. Обе ссылки nullable:
    пустой класс = все классы в указанной отрасли; пустая отрасль = этот класс
    во всех отраслях; хотя бы одно поле должно быть заполнено.
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
        null=True,
        blank=True,
        related_name="eng_function_competencies",
        verbose_name="Класс систем",
        help_text="Пусто — все классы (в указанной отрасли).",
    )
    industry = models.ForeignKey(
        "categories.Category",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="eng_function_competencies",
        verbose_name="Индустрия",
        help_text="Индустрия — категория 1-го уровня. Пусто — все отрасли.",
    )

    class Meta:
        """Мета-настройки модели."""
        verbose_name = "Компетенция инж. компании по функции"
        verbose_name_plural = "Компетенции инж. компании по функции"
        ordering = ["system_class__level", "system_class__system_class", "industry__category_name"]

    def __str__(self):
        """Строковое представление объекта («класс · индустрия», с «Все»)."""
        cls = self.system_class.system_class if self.system_class else "Все классы"
        ind = self.industry.category_name if self.industry else "Все отрасли"
        return f"{cls} · {ind}"


class FullCycleVendorProfile(models.Model):
    """Профиль вендора полного цикла (тип full_cycle_vendor).

    Dedicated OneToOne profile (region + resident_object) + products M2M
    + separate FullCycleFunctionCompetency (аналогично EngineeringCompanyProfile + FunctionCompetency).
    """

    entity = models.OneToOneField(
        Entity,
        on_delete=models.CASCADE,
        related_name="full_cycle_profile",
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
        related_name="resident_full_cycle_vendors",
        verbose_name="Вхожий объект",
        help_text="Объект, на котором компания уже закрепилась и работает.",
    )
    products = models.ManyToManyField(
        "system.VendorProduct",
        blank=True,
        related_name="full_cycle_competent_vendors",
        verbose_name="Узкая компетенция по продуктам",
    )

    class Meta:
        """Мета-настройки модели."""
        verbose_name = "Профиль вендора полного цикла"
        verbose_name_plural = "Профили вендоров полного цикла"

    def __str__(self):
        """Строковое представление объекта."""
        return f"FullCycleVendorProfile: {self.entity.entity_name}"


class FullCycleFunctionCompetency(models.Model):
    """Узкая компетенция вендора полного цикла по функции: пара «класс + индустрия».

    Каждая строка — одна связанная пара (напр. MES · Нефтехимия).
    """

    profile = models.ForeignKey(
        FullCycleVendorProfile,
        on_delete=models.CASCADE,
        related_name="function_competencies",
        verbose_name="Профиль вендора полного цикла",
    )
    system_class = models.ForeignKey(
        "system.AutomationClass",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="full_cycle_function_competencies",
        verbose_name="Класс систем",
        help_text="Пусто — все классы (в указанной отрасли).",
    )
    industry = models.ForeignKey(
        "categories.Category",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="full_cycle_function_competencies",
        verbose_name="Индустрия",
        help_text="Индустрия — категория 1-го уровня. Пусто — все отрасли.",
    )

    class Meta:
        """Мета-настройки модели."""
        verbose_name = "Компетенция по функции (полный цикл)"
        verbose_name_plural = "Компетенции по функции (полный цикл)"
        ordering = ["system_class__level", "system_class__system_class", "industry__category_name"]

    def __str__(self):
        """Строковое представление объекта («класс · индустрия», с «Все»)."""
        cls = self.system_class.system_class if self.system_class else "Все классы"
        ind = self.industry.category_name if self.industry else "Все отрасли"
        return f"{cls} · {ind}"
