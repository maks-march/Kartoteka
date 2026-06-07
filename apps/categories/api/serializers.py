from rest_framework import serializers


class CategoryInputSerializer(serializers.Serializer):
    name = serializers.CharField(min_length=2, max_length=100)
    level = serializers.IntegerField(min_value=1, max_value=3)


class CategoryOutputSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    level = serializers.IntegerField()
    objects_count = serializers.IntegerField(required=False, default=0)
