"""Сериализаторы участников рынка для REST API."""
from rest_framework import serializers

from apps.entities.models import (
    Entity, EngineeringCompanyProfile, FunctionCompetency,
    FullCycleVendorProfile, FullCycleFunctionCompetency,
)


class FunctionCompetencySerializer(serializers.ModelSerializer):
    system_class_name = serializers.CharField(source="system_class.system_class", read_only=True)

    class Meta:
        model = FunctionCompetency
        fields = ["id", "system_class", "system_class_name", "industry"]


class FullCycleFunctionCompetencySerializer(serializers.ModelSerializer):
    system_class_name = serializers.CharField(source="system_class.system_class", read_only=True)

    class Meta:
        model = FullCycleFunctionCompetency
        fields = ["id", "system_class", "system_class_name", "industry"]


class EngineeringProfileSerializer(serializers.ModelSerializer):
    """Чтение профиля инжиниринговой компании."""
    resident_object_name = serializers.CharField(source="resident_object.name", read_only=True)
    product_competencies = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    function_competencies = FunctionCompetencySerializer(many=True, read_only=True)

    class Meta:
        model = EngineeringCompanyProfile
        fields = [
            "id", "region", "resident_object", "resident_object_name",
            "product_competencies", "function_competencies",
        ]


class FullCycleProfileSerializer(serializers.ModelSerializer):
    """Чтение dedicated профиля вендора полного цикла."""
    resident_object_name = serializers.CharField(source="resident_object.name", read_only=True)
    products = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    function_competencies = FullCycleFunctionCompetencySerializer(many=True, read_only=True)

    class Meta:
        model = FullCycleVendorProfile
        fields = [
            "id", "region", "resident_object", "resident_object_name",
            "products", "function_competencies",
        ]


class EntitySerializer(serializers.ModelSerializer):
    entity_type_display = serializers.CharField(source="get_entity_type_display", read_only=True)
    # Профили типов (только чтение, показываются при наличии).
    engineering_profile = EngineeringProfileSerializer(read_only=True)
    full_cycle_profile = FullCycleProfileSerializer(read_only=True)
    products = serializers.SerializerMethodField()

    class Meta:
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


class EntityCreateUpdateSerializer(serializers.Serializer):
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
    industries = serializers.JSONField(required=False, allow_null=True)

    def validate_inn(self, value):
        # Пустой ИНН храним как NULL (unique допускает несколько NULL).
        if value in (None, ""):
            return None
        return value


class FunctionCompetencyWriteSerializer(serializers.Serializer):
    system_class = serializers.IntegerField()
    industry = serializers.CharField(max_length=255)


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
