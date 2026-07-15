"""Сериализаторы категорий для REST API."""
from rest_framework import serializers

from apps.categories.models import Category


class CategorySerializer(serializers.ModelSerializer):
    """Представление категории для чтения через API."""
    class Meta:
        """Мета-настройки модели/сериализатора."""
        model = Category
        fields = ["id", "category_name", "object_level"]


class CategoryCreateUpdateSerializer(serializers.Serializer):
    """Валидация данных при создании/обновлении категории."""
    category_name = serializers.CharField(max_length=255)
    object_level = serializers.IntegerField(min_value=1, max_value=3)
