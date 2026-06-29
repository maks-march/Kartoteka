from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny

from apps.system.api.serializers import (
    SystemListSerializer,
    SystemDetailSerializer,
    SystemCreateUpdateSerializer,
    SystemAttachObjectSerializer,
    AutomationClassSerializer,
)
from apps.system.usecases.system_usecase import SystemUseCase
from apps.system.usecases.automation_class_usecase import AutomationClassUseCase
from apps.objects.usecases.object_system_usecase import ObjectSystemUseCase
from apps.objects.api.serializers import ObjectSystemSerializer


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
        obj = request.query_params.getlist("object") or None
        vendor = request.query_params.getlist("vendor") or None
        system_status = request.query_params.getlist("system_status") or None
        product_type = request.query_params.getlist("product_type") or None
        ordering = request.query_params.getlist("ordering") or None
        usecase = SystemUseCase()
        systems = usecase.list(
            system_class=system_class,
            search=search,
            obj=obj,
            vendor=vendor,
            system_status=system_status,
            product_type=product_type,
            ordering=ordering,
        )
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
        obj = usecase.update(pk, request.user, **serializer.validated_data)
        return Response(SystemDetailSerializer(obj).data)

    def delete(self, request, pk):
        usecase = SystemUseCase()
        usecase.delete(pk, request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class SystemAttachObjectView(APIView):
    """Привязать существующий объект к системе (создать связь ObjectSystem)."""

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        system_usecase = SystemUseCase()
        system = system_usecase.get(pk)

        serializer = SystemAttachObjectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        os_usecase = ObjectSystemUseCase()
        link = os_usecase.attach(
            object_pk=data.pop("object"),
            system_pk=system.pk,
            **data,
        )
        return Response(
            ObjectSystemSerializer(link).data, status=status.HTTP_201_CREATED
        )
