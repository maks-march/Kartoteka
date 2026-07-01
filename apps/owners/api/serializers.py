"""Сериализаторы юридических лиц для REST API."""
from rest_framework import serializers

from apps.owners.models import OwnerEntity


class OwnerEntitySerializer(serializers.ModelSerializer):
    owner_name_display = serializers.CharField(source="owner.owner_name", read_only=True)
    ultimate_owner_name = serializers.CharField(source="ultimate_owner.owner_name", read_only=True)

    class Meta:
        model = OwnerEntity
        fields = [
            "id",
            "owner_name",
            "owner",
            "owner_name_display",
            "ultimate_owner",
            "ultimate_owner_name",
        ]


class OwnerEntityCreateUpdateSerializer(serializers.Serializer):
    owner_name = serializers.CharField(max_length=255)
    owner = serializers.IntegerField(required=False, allow_null=True)
    ultimate_owner = serializers.IntegerField(required=False, allow_null=True)


class OwnerEntityAttachObjectSerializer(serializers.Serializer):
    object = serializers.IntegerField()
