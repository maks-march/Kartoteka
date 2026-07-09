"""Сериализаторы категорий для REST API."""
from rest_framework import serializers

from apps.categories.models import Category


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "category_name", "object_level"]


class CategoryCreateUpdateSerializer(serializers.Serializer):
    category_name = serializers.CharField(max_length=255)
    object_level = serializers.IntegerField(min_value=1, max_value=3)
