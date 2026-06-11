from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny

from apps.system.api.serializers import (
    SystemListSerializer,
    SystemDetailSerializer,
    SystemCreateUpdateSerializer,
    AutomationClassSerializer,
)
from apps.system.usecases.system_usecase import SystemUseCase
from apps.system.usecases.automation_class_usecase import AutomationClassUseCase


class AutomationClassListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        usecase = AutomationClassUseCase()
        classes = usecase.list()
        serializer = AutomationClassSerializer(classes, many=True)
        return Response(serializer.data)


class SystemListCreateView(APIView):
    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated()]
        return [AllowAny()]

    def get(self, request):
        system_class = request.query_params.get("system_class")
        search = request.query_params.get("search")
        usecase = SystemUseCase()
        systems = usecase.list(system_class=system_class, search=search)
        serializer = SystemListSerializer(systems, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = SystemCreateUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        usecase = SystemUseCase()
        obj = usecase.create(user=request.user, **serializer.validated_data)
        return Response(
            SystemDetailSerializer(obj).data, status=status.HTTP_201_CREATED
        )


class SystemDetailView(APIView):
    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAuthenticated()]

    def get(self, request, pk):
        usecase = SystemUseCase()
        obj = usecase.get(pk)
        serializer = SystemDetailSerializer(obj)
        return Response(serializer.data)

    def patch(self, request, pk):
        serializer = SystemCreateUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        usecase = SystemUseCase()
        obj = usecase.update(pk, **serializer.validated_data)
        return Response(SystemDetailSerializer(obj).data)

    def delete(self, request, pk):
        usecase = SystemUseCase()
        usecase.delete(pk)
        return Response(status=status.HTTP_204_NO_CONTENT)
