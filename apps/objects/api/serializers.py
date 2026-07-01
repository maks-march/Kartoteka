"""Сериализаторы объектов и связей «система на объекте» для REST API."""
from rest_framework import serializers

from apps.objects.models import Object, ObjectSystem


class ObjectListSerializer(serializers.ModelSerializer):
    parent_name = serializers.CharField(source="parent.name", read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True)
    owner_entity_name = serializers.CharField(source="owner_entity.owner_name", read_only=True)

    class Meta:
        model = Object
        fields = [
            "id",
            "name",
            "object_short_name",
            "object_class",
            "level",
            "parent",
            "parent_name",
            "category",
            "category_name",
            "owner_entity",
            "owner_entity_name",
            "status",
            "city",
            "created_at",
        ]


class ObjectDetailSerializer(serializers.ModelSerializer):
    parent_name = serializers.CharField(source="parent.name", read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True)
    owner_entity_name = serializers.CharField(source="owner_entity.owner_name", read_only=True)
    children = serializers.SerializerMethodField()
    creator_id_username = serializers.CharField(
        source="creator_id.username", read_only=True
    )

    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Object
        fields = [
            "id",
            "name",
            "object_short_name",
            "object_old_name",
            "object_law_name",
            "object_class",
            "level",
            "parent",
            "parent_name",
            "category",
            "category_name",
            "owner_entity",
            "owner_entity_name",
            # характеристики
            "start_date",
            "is_reconstructed",
            "capacity",
            "status",
            "status_display",
            "notes",
            # адрес
            "country",
            "region",
            "city",
            "street",
            "house",
            "title",
            "fias_code",
            "children",
            "creator_id",
            "creator_id_username",
            "created_at",
            "updated_at",
        ]

    def get_children(self, obj):
        qs = obj.children.filter(is_deleted=False)
        return ObjectListSerializer(qs, many=True).data


class _ObjectExtraFieldsMixin(serializers.Serializer):
    """Дополнительные (описательные/характеристики/адрес) поля объекта."""

    object_short_name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    object_old_name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    object_law_name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    object_class = serializers.CharField(max_length=255, required=False, allow_blank=True)

    start_date = serializers.DateField(required=False, allow_null=True)
    is_reconstructed = serializers.BooleanField(required=False)
    capacity = serializers.CharField(max_length=255, required=False, allow_blank=True)
    status = serializers.ChoiceField(choices=Object.STATUS_CHOICES, required=False)
    notes = serializers.CharField(required=False, allow_blank=True)

    country = serializers.CharField(max_length=255, required=False, allow_blank=True)
    region = serializers.CharField(max_length=255, required=False, allow_blank=True)
    city = serializers.CharField(max_length=255, required=False, allow_blank=True)
    street = serializers.CharField(max_length=255, required=False, allow_blank=True)
    house = serializers.CharField(max_length=255, required=False, allow_blank=True)
    title = serializers.CharField(max_length=255, required=False, allow_blank=True)
    fias_code = serializers.CharField(max_length=255, required=False, allow_blank=True)


class ObjectCreateSerializer(_ObjectExtraFieldsMixin):
    name = serializers.CharField(max_length=255)
    level = serializers.IntegerField(min_value=1, max_value=3)
    parent = serializers.IntegerField(required=False, allow_null=True)
    category = serializers.IntegerField(required=False, allow_null=True)
    owner_entity = serializers.IntegerField(required=False, allow_null=True)


class ObjectUpdateSerializer(_ObjectExtraFieldsMixin):
    name = serializers.CharField(max_length=255, required=False)
    level = serializers.IntegerField(min_value=1, max_value=3, required=False)
    parent = serializers.IntegerField(required=False, allow_null=True)
    category = serializers.IntegerField(required=False, allow_null=True)
    owner_entity = serializers.IntegerField(required=False, allow_null=True)


class ObjectSystemSerializer(serializers.ModelSerializer):
    object_name = serializers.CharField(source="object.name", read_only=True)
    system_name = serializers.CharField(source="system.autosystem_name", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    integrator_name = serializers.CharField(source="integrator.participant_name", read_only=True)
    implimentor_name = serializers.CharField(source="implimentor.participant_name", read_only=True)

    class Meta:
        model = ObjectSystem
        fields = [
            "id",
            "object",
            "object_name",
            "system",
            "system_name",
            "status",
            "status_display",
            "implementation_date",
            "integrator",
            "integrator_name",
            "implimentor",
            "implimentor_name",
        ]


class ObjectSystemCreateSerializer(serializers.Serializer):
    object = serializers.IntegerField()
    system = serializers.IntegerField()
    status = serializers.ChoiceField(
        choices=ObjectSystem.STATUS_CHOICES, required=False, default="planned"
    )
    implementation_date = serializers.DateField(required=False, allow_null=True)
    integrator = serializers.IntegerField(required=False, allow_null=True)
    implimentor = serializers.IntegerField(required=False, allow_null=True)


class ObjectSystemUpdateSerializer(serializers.Serializer):
    object = serializers.IntegerField(required=False)
    system = serializers.IntegerField(required=False)
    status = serializers.ChoiceField(choices=ObjectSystem.STATUS_CHOICES, required=False)
    implementation_date = serializers.DateField(required=False, allow_null=True)
    integrator = serializers.IntegerField(required=False, allow_null=True)
    implimentor = serializers.IntegerField(required=False, allow_null=True)
