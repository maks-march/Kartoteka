from rest_framework import serializers

from apps.objects.models import Object


class ObjectListSerializer(serializers.ModelSerializer):
    parent_name = serializers.CharField(source="parent.name", read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True)
    owner_entity_name = serializers.CharField(source="owner_entity.owner_name", read_only=True)

    class Meta:
        model = Object
        fields = [
            "id",
            "name",
            "level",
            "parent",
            "parent_name",
            "category",
            "category_name",
            "owner_entity",
            "owner_entity_name",
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

    class Meta:
        model = Object
        fields = [
            "id",
            "name",
            "level",
            "parent",
            "parent_name",
            "category",
            "category_name",
            "owner_entity",
            "owner_entity_name",
            "children",
            "creator_id",
            "creator_id_username",
            "created_at",
            "updated_at",
        ]

    def get_children(self, obj):
        qs = obj.children.filter(is_deleted=False)
        return ObjectListSerializer(qs, many=True).data


class ObjectCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    level = serializers.IntegerField(min_value=1, max_value=3)
    parent = serializers.IntegerField(required=False, allow_null=True)
    category = serializers.IntegerField(required=False, allow_null=True)
    owner_entity = serializers.IntegerField(required=False, allow_null=True)


class ObjectUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255, required=False)
    level = serializers.IntegerField(min_value=1, max_value=3, required=False)
    parent = serializers.IntegerField(required=False, allow_null=True)
    category = serializers.IntegerField(required=False, allow_null=True)
    owner_entity = serializers.IntegerField(required=False, allow_null=True)
