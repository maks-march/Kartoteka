"""Сериализаторы категорий для REST API."""
from rest_framework import serializers

from apps.categories.models import Category


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "level"]


class CategoryCreateUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    level = serializers.IntegerField(min_value=1, max_value=3)
