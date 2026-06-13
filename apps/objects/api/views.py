from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny

from apps.objects.api.serializers import (
    ObjectListSerializer,
    ObjectDetailSerializer,
    ObjectCreateSerializer,
    ObjectUpdateSerializer,
)
from apps.objects.usecases.object_usecase import ObjectUseCase


class ObjectListCreateView(APIView):
    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated()]
        return [AllowAny()]

    def get(self, request):
        level = request.query_params.get("level") or None
        search = request.query_params.get("search") or None
        category = request.query_params.getlist("category") or None
        system = request.query_params.getlist("system") or None
        usecase = ObjectUseCase()
        objects = usecase.list(level=level, search=search, category=category, system=system)
        serializer = ObjectListSerializer(objects, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = ObjectCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        usecase = ObjectUseCase()
        obj = usecase.create(request.user, **serializer.validated_data)
        return Response(
            ObjectDetailSerializer(obj).data, status=status.HTTP_201_CREATED
        )


class ObjectDetailView(APIView):
    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAuthenticated()]

    def get(self, request, pk):
        usecase = ObjectUseCase()
        obj = usecase.get(pk)
        serializer = ObjectDetailSerializer(obj)
        return Response(serializer.data)

    def patch(self, request, pk):
        serializer = ObjectUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        usecase = ObjectUseCase()
        obj = usecase.update(pk, request.user, **serializer.validated_data)
        return Response(ObjectDetailSerializer(obj).data)

    def delete(self, request, pk):
        usecase = ObjectUseCase()
        usecase.delete(pk, request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)
