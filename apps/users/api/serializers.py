"""Сериализаторы аутентификации (регистрация, вход) для REST API."""
from rest_framework import serializers


class RegisterSerializer(serializers.Serializer):
    """Валидация данных регистрации (логин, пароль)."""
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True)


class LoginSerializer(serializers.Serializer):
    """Валидация данных входа (логин, пароль)."""
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True)
