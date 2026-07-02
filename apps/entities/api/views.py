"""REST API участников рынка."""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny

from apps.entities.api.serializers import (
    EntitySerializer,
    EntityCreateUpdateSerializer,
)
from apps.entities.usecases.entity_usecase import EntityUseCase


class EntityListCreateView(APIView):
    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated()]
        return [AllowAny()]

    def get(self, request):
        search = request.query_params.get("search")
        ordering = request.query_params.getlist("ordering") or None
        usecase = EntityUseCase()
        entities = usecase.list(search=search, ordering=ordering)
        serializer = EntitySerializer(entities, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = EntityCreateUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        usecase = EntityUseCase()
        obj = usecase.create(**serializer.validated_data)
        return Response(EntitySerializer(obj).data, status=status.HTTP_201_CREATED)


class EntityDetailView(APIView):
    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAuthenticated()]

    def get(self, request, pk):
        usecase = EntityUseCase()
        obj = usecase.get(pk)
        return Response(EntitySerializer(obj).data)

    def patch(self, request, pk):
        serializer = EntityCreateUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        usecase = EntityUseCase()
        obj = usecase.update(pk, **serializer.validated_data)
        return Response(EntitySerializer(obj).data)

    def delete(self, request, pk):
        usecase = EntityUseCase()
        usecase.delete(pk)
        return Response(status=status.HTTP_204_NO_CONTENT)
