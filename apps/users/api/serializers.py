"""Сериализаторы для users API."""

from rest_framework import serializers


class RegisterInputSerializer(serializers.Serializer):
    username = serializers.CharField(min_length=3, max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(min_length=8, write_only=True)

    def validate_username(self, value):
        if not value.isalnum() and "_" not in value:
            raise serializers.ValidationError("Username может содержать только буквы, цифры и _")
        return value


class LoginInputSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


class UserOutputSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()
    email = serializers.EmailField()
    is_staff = serializers.BooleanField()


class TokenOutputSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()
