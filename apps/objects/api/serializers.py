from rest_framework import serializers


class ObjectInputSerializer(serializers.Serializer):
    name = serializers.CharField(min_length=2, max_length=200)
    level = serializers.IntegerField(min_value=1, max_value=3)
    category_id = serializers.IntegerField()


class ObjectOutputSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    level = serializers.IntegerField()
    category_id = serializers.IntegerField()
    category_name = serializers.CharField()

    def to_representation(self, instance):
        """Поддержка и Entity, и dict."""
        if hasattr(instance, "__dict__"):
            data = {
                "id": getattr(instance, "id", None),
                "name": instance.name if hasattr(instance, "name") else getattr(instance, "name", ""),
                "level": instance.level if hasattr(instance, "level") else getattr(instance, "level", 1),
                "category_id": instance.category_id if hasattr(instance, "category_id") else getattr(instance, "category_id", None),
                "category_name": instance.category_name if hasattr(instance, "category_name") else getattr(instance, "category_name", ""),
            }
            return data
        return super().to_representation(instance)
