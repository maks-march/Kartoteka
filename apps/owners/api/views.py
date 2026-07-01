"""REST API юридических лиц (владельцев)."""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny

from apps.owners.api.serializers import (
    OwnerEntitySerializer,
    OwnerEntityCreateUpdateSerializer,
    OwnerEntityAttachObjectSerializer,
)
from apps.owners.usecases.owner_entity_usecase import OwnerEntityUseCase
from apps.objects.usecases.object_usecase import ObjectUseCase
from apps.objects.api.serializers import ObjectListSerializer


class OwnerEntityListCreateView(APIView):
    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated()]
        return [AllowAny()]

    def get(self, request):
        search = request.query_params.get("search")
        ordering = request.query_params.getlist("ordering") or None
        usecase = OwnerEntityUseCase()
        owner_entities = usecase.list(search=search, ordering=ordering)
        serializer = OwnerEntitySerializer(owner_entities, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = OwnerEntityCreateUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        usecase = OwnerEntityUseCase()
        obj = usecase.create(**serializer.validated_data)
        return Response(OwnerEntitySerializer(obj).data, status=status.HTTP_201_CREATED)


class OwnerEntityDetailView(APIView):
    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAuthenticated()]

    def get(self, request, pk):
        usecase = OwnerEntityUseCase()
        obj = usecase.get(pk)
        return Response(OwnerEntitySerializer(obj).data)

    def patch(self, request, pk):
        serializer = OwnerEntityCreateUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        usecase = OwnerEntityUseCase()
        obj = usecase.update(pk, **serializer.validated_data)
        return Response(OwnerEntitySerializer(obj).data)

    def delete(self, request, pk):
        usecase = OwnerEntityUseCase()
        usecase.delete(pk)
        return Response(status=status.HTTP_204_NO_CONTENT)


class OwnerEntityAttachObjectView(APIView):
    """Привязать существующий объект к юридическому лицу."""

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        owner_usecase = OwnerEntityUseCase()
        owner_entity = owner_usecase.get(pk)

        serializer = OwnerEntityAttachObjectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        object_usecase = ObjectUseCase()
        obj = object_usecase.update(
            pk=serializer.validated_data["object"],
            user=request.user,
            owner_entity=owner_entity.pk,
        )
        return Response(ObjectListSerializer(obj).data, status=status.HTTP_200_OK)
