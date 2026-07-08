"""Сериализаторы систем, классов автоматизации и продуктов для REST API."""
from rest_framework import serializers

from apps.system.models import AutomationSystem, AutomationClass, VendorProduct
from apps.objects.models import ObjectSystem


class AutomationClassSerializer(serializers.ModelSerializer):
    label = serializers.CharField(read_only=True)

    class Meta:
        model = AutomationClass
        fields = ["id", "level", "system_class", "name_ru", "label",
                  "description", "is_composite", "includes"]


class VendorProductSerializer(serializers.ModelSerializer):
    # vendor в API — это id УЧАСТНИКА (Entity), а не VendorProfile,
    # чтобы read/write были симметричны. Внутри модели связь идёт через
    # VendorProfile (vendor.entity_id).
    vendor = serializers.IntegerField(source="vendor.entity_id", read_only=True)
    vendor_name = serializers.CharField(source="vendor.entity_name", read_only=True)
    product_type_display = serializers.CharField(source="get_product_type_display", read_only=True)
    system_class_name = serializers.CharField(source="system_class.system_class", read_only=True)

    class Meta:
        model = VendorProduct
        fields = [
            "id", "product_name", "vendor", "vendor_name",
            "product_type", "product_type_display",
            "system_class", "system_class_name", "subsystem_classes",
            "description", "version", "release_year", "end_of_support",
            "technical_specs", "industries",
        ]


class VendorProductCreateUpdateSerializer(serializers.Serializer):
    product_name = serializers.CharField(max_length=255)
    vendor = serializers.IntegerField(required=False, allow_null=True)
    product_type = serializers.ChoiceField(
        choices=VendorProduct.PRODUCT_TYPE_CHOICES, required=False, allow_blank=True
    )
    system_class = serializers.IntegerField(required=False, allow_null=True)
    subsystem_classes = serializers.ListField(
        child=serializers.IntegerField(), required=False
    )
    description = serializers.CharField(required=False, allow_blank=True)
    version = serializers.CharField(max_length=255, required=False, allow_blank=True)
    release_year = serializers.DateField(required=False, allow_null=True)
    end_of_support = serializers.DateField(required=False, allow_null=True)
    technical_specs = serializers.DictField(required=False, allow_null=True)
    industries = serializers.ListField(
        child=serializers.CharField(), required=False, allow_null=True
    )


class SystemListSerializer(serializers.ModelSerializer):
    class_name = serializers.CharField(source="system_class.system_class", read_only=True)
    class_level = serializers.IntegerField(source="system_class.level", read_only=True)
    product_name = serializers.CharField(source="product.product_name", read_only=True)
    status_display = serializers.CharField(source="get_system_status_display", read_only=True)

    class Meta:
        model = AutomationSystem
        fields = [
            "id", "autosystem_name", "autosystem_short_name",
            "system_class", "class_name", "class_level",
            "product", "product_name",
            "system_status", "status_display",
        ]


class SystemDetailSerializer(serializers.ModelSerializer):
    system_class_detail = AutomationClassSerializer(source="system_class", read_only=True)
    product_name = serializers.CharField(source="product.product_name", read_only=True)
    status_display = serializers.CharField(source="get_system_status_display", read_only=True)

    subsystem_classes_detail = AutomationClassSerializer(
        source="subsystem_classes", many=True, read_only=True
    )

    class Meta:
        model = AutomationSystem
        fields = [
            "id", "autosystem_name", "autosystem_short_name",
            "system_class", "system_class_detail",
            "subsystem_classes", "subsystem_classes_detail",
            "product", "product_name",
            "system_status", "status_display",
            "notes", "release_year",
            "technical_specs", "modules", "interfaces",
        ]


class SystemCreateUpdateSerializer(serializers.Serializer):
    autosystem_name = serializers.CharField(max_length=255)
    autosystem_short_name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    system_class = serializers.IntegerField()
    subsystem_classes = serializers.ListField(
        child=serializers.IntegerField(), required=False
    )
    product = serializers.IntegerField(required=False, allow_null=True)
    system_status = serializers.ChoiceField(choices=AutomationSystem.STATUS_CHOICES, required=False)
    notes = serializers.CharField(required=False, allow_blank=True)
    release_year = serializers.DateField(required=False, allow_null=True)
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
