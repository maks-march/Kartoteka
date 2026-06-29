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
    status_display = serializers.CharField(source="get_system_status_display", read_only=True)
    product_type_display = serializers.CharField(source="get_product_type_display", read_only=True)

    class Meta:
        model = AutomatedSystem
        fields = [
            "id", "autosystem_name", "autosystem_short_name",
            "system_class", "class_name", "class_level",
            "vendor", "vendor_name", "version",
            "system_status", "status_display",
            "product_type", "product_type_display",
        ]


class SystemDetailSerializer(serializers.ModelSerializer):
    system_class_detail = AutomationClassSerializer(source="system_class", read_only=True)
    vendor_name = serializers.CharField(source="vendor.participant_name", read_only=True)
    status_display = serializers.CharField(source="get_system_status_display", read_only=True)
    product_type_display = serializers.CharField(source="get_product_type_display", read_only=True)

    class Meta:
        model = AutomatedSystem
        fields = [
            "id", "autosystem_name", "autosystem_short_name",
            "system_class", "system_class_detail",
            "vendor", "vendor_name", "version",
            "system_status", "status_display",
            "product_type", "product_type_display",
            "notes", "release_year", "end_of_support",
            "article", "technical_specs", "modules", "interfaces",
        ]


class SystemCreateUpdateSerializer(serializers.Serializer):
    autosystem_name = serializers.CharField(max_length=255)
    autosystem_short_name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    system_class = serializers.IntegerField()
    vendor = serializers.IntegerField(required=False, allow_null=True)
    version = serializers.CharField(max_length=255, required=False, allow_blank=True)
    system_status = serializers.ChoiceField(choices=AutomatedSystem.STATUS_CHOICES, required=False)
    product_type = serializers.ChoiceField(choices=AutomatedSystem.PRODUCT_TYPE_CHOICES, required=False)
    notes = serializers.CharField(required=False, allow_blank=True)
    release_year = serializers.DateField(required=False, allow_null=True)
    end_of_support = serializers.DateField(required=False, allow_null=True)
    article = serializers.CharField(max_length=255, required=False, allow_blank=True, allow_null=True)
    technical_specs = serializers.JSONField(required=False, allow_null=True)
    modules = serializers.JSONField(required=False, allow_null=True)
    interfaces = serializers.JSONField(required=False, allow_null=True)


class SystemAttachObjectSerializer(serializers.Serializer):
    object = serializers.IntegerField()
    status = serializers.ChoiceField(
        choices=ObjectSystem.STATUS_CHOICES, required=False, default="planned"
    )
    implementation_date = serializers.DateField(required=False, allow_null=True)
    integrator = serializers.IntegerField(required=False, allow_null=True)
    implimentor = serializers.IntegerField(required=False, allow_null=True)
