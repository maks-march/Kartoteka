from rest_framework import serializers

from apps.system.models import AutomatedSystem, AutomationClass
from apps.objects.models import ObjectSystem


class AutomationClassSerializer(serializers.ModelSerializer):
    class Meta:
        model = AutomationClass
        fields = ["id", "level", "system_class", "description"]


class SystemListSerializer(serializers.ModelSerializer):
    class_name = serializers.CharField(source="system_class.system_class", read_only=True)
    class_level = serializers.IntegerField(source="system_class.level", read_only=True)
    vendor_name = serializers.CharField(source="vendor.participant_name", read_only=True)

    class Meta:
        model = AutomatedSystem
        fields = ["id", "autosystem_name", "system_class", "class_name", "class_level", "vendor", "vendor_name"]


class SystemDetailSerializer(serializers.ModelSerializer):
    system_class_detail = AutomationClassSerializer(source="system_class", read_only=True)
    vendor_name = serializers.CharField(source="vendor.participant_name", read_only=True)

    class Meta:
        model = AutomatedSystem
        fields = ["id", "autosystem_name", "system_class", "system_class_detail", "vendor", "vendor_name"]


class SystemCreateUpdateSerializer(serializers.Serializer):
    autosystem_name = serializers.CharField(max_length=255)
    system_class = serializers.IntegerField()
    vendor = serializers.IntegerField(required=False, allow_null=True)


class SystemAttachObjectSerializer(serializers.Serializer):
    object = serializers.IntegerField()
    status = serializers.ChoiceField(
        choices=ObjectSystem.STATUS_CHOICES, required=False, default="planned"
    )
    implementation_date = serializers.DateField(required=False, allow_null=True)
    integrator = serializers.IntegerField(required=False, allow_null=True)
    implimentor = serializers.IntegerField(required=False, allow_null=True)
