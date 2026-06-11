from rest_framework import serializers

from apps.system.models import AutomatedSystem, AutomationClass


class AutomationClassSerializer(serializers.ModelSerializer):
    class Meta:
        model = AutomationClass
        fields = ["id", "level", "system_class", "description"]


class SystemListSerializer(serializers.ModelSerializer):
    class_name = serializers.CharField(source="system_class.system_class", read_only=True)
    class_level = serializers.IntegerField(source="system_class.level", read_only=True)

    class Meta:
        model = AutomatedSystem
        fields = ["id", "autosystem_name", "system_class", "class_name", "class_level"]


class SystemDetailSerializer(serializers.ModelSerializer):
    system_class_detail = AutomationClassSerializer(source="system_class", read_only=True)

    class Meta:
        model = AutomatedSystem
        fields = ["id", "autosystem_name", "system_class", "system_class_detail"]


class SystemCreateUpdateSerializer(serializers.Serializer):
    autosystem_name = serializers.CharField(max_length=255)
    system_class = serializers.IntegerField()
