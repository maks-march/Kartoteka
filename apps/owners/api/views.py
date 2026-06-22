from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny

from apps.owners.api.serializers import (
    OwnerEntitySerializer,
    OwnerEntityCreateUpdateSerializer,
)
from apps.owners.usecases.owner_entity_usecase import OwnerEntityUseCase


class OwnerEntityListCreateView(APIView):
    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated()]
        return [AllowAny()]

    def get(self, request):
        search = request.query_params.get("search")
        usecase = OwnerEntityUseCase()
        owner_entities = usecase.list(search=search)
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
