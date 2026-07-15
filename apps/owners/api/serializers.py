"""Сериализаторы юридических лиц для REST API."""
from rest_framework import serializers

from apps.owners.models import OwnerEntity


class OwnerEntitySerializer(serializers.ModelSerializer):
    """Представление юр. лица для чтения через API."""
    owner_name_display = serializers.CharField(source="owner.owner_name", read_only=True)
    ultimate_owner_name = serializers.CharField(source="ultimate_owner.owner_name", read_only=True)

    class Meta:
        """Мета-настройки модели/сериализатора."""
        model = OwnerEntity
        fields = [
            "id",
            "owner_name",
            "owner",
            "owner_name_display",
            "ultimate_owner",
            "ultimate_owner_name",
            "is_root",
        ]
        read_only_fields = ["is_root"]


class OwnerEntityCreateUpdateSerializer(serializers.Serializer):
    """Валидация данных при создании/обновлении юр. лица."""
    owner_name = serializers.CharField(max_length=255)
    owner = serializers.IntegerField(required=False, allow_null=True)
    ultimate_owner = serializers.IntegerField(required=False, allow_null=True)


class OwnerEntityAttachObjectSerializer(serializers.Serializer):
    """Валидация id объекта при привязке к юр. лицу."""
    object = serializers.IntegerField()
