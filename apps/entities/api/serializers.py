"""Сериализаторы участников рынка для REST API."""
from rest_framework import serializers

from apps.entities.models import (
    Entity, EngineeringCompanyProfile, EngineeringCompanyFunctionCompetency,
    FullCycleVendorProfile, FullCycleFunctionCompetency,
    SupplierProfile, SystemIntegratorProfile,
)


class FunctionCompetencySerializer(serializers.ModelSerializer):
    """Представление компетенции по функции (инж. компания) для чтения."""
    system_class_name = serializers.CharField(source="system_class.system_class", read_only=True)
    industry_name = serializers.CharField(source="industry.category_name", read_only=True)

    class Meta:
        """Поля сериализатора."""
        model = EngineeringCompanyFunctionCompetency
        fields = ["id", "system_class", "system_class_name", "industry", "industry_name"]


class FullCycleFunctionCompetencySerializer(serializers.ModelSerializer):
    """Представление компетенции по функции (вендор полного цикла)."""
    system_class_name = serializers.CharField(source="system_class.system_class", read_only=True)
    industry_name = serializers.CharField(source="industry.category_name", read_only=True)

    class Meta:
        """Поля сериализатора."""
        model = FullCycleFunctionCompetency
        fields = ["id", "system_class", "system_class_name", "industry", "industry_name"]


class SupplierProfileSerializer(serializers.ModelSerializer):
    """Чтение профиля поставщика."""
    products = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        """Поля сериализатора."""
        model = SupplierProfile
        fields = ["id", "products"]


class SystemIntegratorProfileSerializer(serializers.ModelSerializer):
    """Чтение профиля системного интегратора."""
    vendor_partners = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        """Поля сериализатора."""
        model = SystemIntegratorProfile
        fields = ["id", "managing_owner", "vendor_partners"]


class EngineeringProfileSerializer(serializers.ModelSerializer):
    """Чтение профиля инжиниринговой компании."""
    resident_object_name = serializers.CharField(source="resident_object.object_name", read_only=True)
    product_competencies = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    function_competencies = FunctionCompetencySerializer(many=True, read_only=True)

    class Meta:
        """Поля сериализатора."""
        model = EngineeringCompanyProfile
        fields = [
            "id", "region", "resident_object", "resident_object_name",
            "product_competencies", "function_competencies",
        ]


class FullCycleProfileSerializer(serializers.ModelSerializer):
    """Чтение dedicated профиля вендора полного цикла."""
    resident_object_name = serializers.CharField(source="resident_object.object_name", read_only=True)
    function_competencies = FullCycleFunctionCompetencySerializer(many=True, read_only=True)

    class Meta:
        """Поля сериализатора."""
        model = FullCycleVendorProfile
        fields = [
            "id", "region", "resident_object", "resident_object_name",
            "function_competencies",
        ]


class EntitySerializer(serializers.ModelSerializer):
    """Полное представление участника рынка с профилями для чтения."""
    entity_type_display = serializers.CharField(source="get_entity_type_display", read_only=True)
    # Профили типов (только чтение, показываются при наличии).
    engineering_profile = EngineeringProfileSerializer(read_only=True)
    full_cycle_profile = FullCycleProfileSerializer(read_only=True)
    products = serializers.SerializerMethodField()
    # Отрасли вычисляются из связей по типу участника (только чтение).
    industries = serializers.SerializerMethodField()

    class Meta:
        """Поля сериализатора."""
        model = Entity
        fields = [
            "id", "entity_name", "inn", "contacts", "registration_date",
            "financial_data", "entity_type", "entity_type_display", "is_partner",
            "website", "kam_name", "kam_phone", "contact_person", "contact_phone",
            "presentation_url", "profile", "industries",
            "engineering_profile", "full_cycle_profile", "products",
        ]

    def get_products(self, obj):
        """Id продуктов вендора (через VendorProfile)."""
        return list(obj.products.values_list("id", flat=True))

    def get_industries(self, obj):
        """Id вычисленных отраслей участника (категории 1-го уровня)."""
        return [c.pk for c in obj.industries]


class EntityCreateUpdateSerializer(serializers.Serializer):
    """Валидация данных при создании/обновлении участника."""
    entity_name = serializers.CharField(max_length=255)
    inn = serializers.CharField(max_length=12, required=False, allow_blank=True, allow_null=True)
    contacts = serializers.JSONField(required=False, allow_null=True)
    registration_date = serializers.DateField(required=False, allow_null=True)
    financial_data = serializers.JSONField(required=False, allow_null=True)
    entity_type = serializers.ChoiceField(choices=Entity.ENTITY_TYPE_CHOICES, required=False, allow_blank=True)
    is_partner = serializers.BooleanField(required=False)
    website = serializers.CharField(max_length=255, required=False, allow_blank=True)
    kam_name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    kam_phone = serializers.CharField(max_length=50, required=False, allow_blank=True)
    contact_person = serializers.CharField(max_length=255, required=False, allow_blank=True)
    contact_phone = serializers.CharField(max_length=50, required=False, allow_blank=True)
    presentation_url = serializers.CharField(max_length=255, required=False, allow_blank=True)
    profile = serializers.CharField(required=False, allow_blank=True)
    # Отрасли участника не задаются напрямую — вычисляются из связей.

    def validate_inn(self, value):
        # Пустой ИНН храним как NULL (unique допускает несколько NULL).
        """Приводит пустой ИНН к None (несколько NULL допустимы уникальностью)."""
        if value in (None, ""):
            return None
        return value


class FunctionCompetencyWriteSerializer(serializers.Serializer):
    """Валидация пары «класс + индустрия» при записи компетенции.

    industry — id категории 1-го уровня (FK).
    """
    system_class = serializers.IntegerField()
    industry = serializers.IntegerField()


class EngineeringProfileWriteSerializer(serializers.Serializer):
    """Запись профиля инжиниринговой компании (region + связи + компетенции)."""
    region = serializers.CharField(required=False, allow_blank=True, default="")
    resident_object = serializers.IntegerField(required=False, allow_null=True)
    product_competencies = serializers.ListField(
        child=serializers.IntegerField(), required=False, default=list
    )
    function_competencies = FunctionCompetencyWriteSerializer(
        many=True, required=False, default=list
    )


class VendorProductsWriteSerializer(serializers.Serializer):
    """Запись продуктов вендора (id продуктов, привязываемых к VendorProfile)."""
    product_ids = serializers.ListField(
        child=serializers.IntegerField(), required=False, default=list
    )


class SupplierProductsWriteSerializer(serializers.Serializer):
    """Запись поставляемых продуктов (M2M со стороны поставщика)."""
    product_ids = serializers.ListField(
        child=serializers.IntegerField(), required=False, default=list
    )


class SystemIntegratorProfileWriteSerializer(serializers.Serializer):
    """Запись профиля системного интегратора."""
    managing_owner = serializers.IntegerField(required=False, allow_null=True)
    vendor_partner_ids = serializers.ListField(
        child=serializers.IntegerField(), required=False, default=list
    )


class FullCycleProfileWriteSerializer(serializers.Serializer):
    """Запись dedicated профиля вендора полного цикла.

    Компетенции по продуктам у ФПЦ нет (убрана) — только регион, вхожий
    объект и компетенции по функции.
    """
    region = serializers.CharField(required=False, allow_blank=True, default="")
    resident_object = serializers.IntegerField(required=False, allow_null=True)
    function_competencies = FunctionCompetencyWriteSerializer(
        many=True, required=False, default=list
    )
