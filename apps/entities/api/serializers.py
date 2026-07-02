"""Сериализаторы участников рынка для REST API."""
from rest_framework import serializers

from apps.entities.models import Entity


class EntitySerializer(serializers.ModelSerializer):
    entity_type_display = serializers.CharField(source="get_entity_type_display", read_only=True)

    class Meta:
        model = Entity
        fields = [
            "id", "entity_name", "inn", "contacts", "registration_date",
            "financial_data", "entity_type", "entity_type_display", "is_partner",
            "website", "kam_name", "kam_phone", "contact_person", "contact_phone",
            "presentation_url", "profile", "industries",
        ]


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
