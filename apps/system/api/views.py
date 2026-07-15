"""REST API автоматизированных систем, справочника классов и продуктов."""
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
    VendorProductSerializer,
    VendorProductCreateUpdateSerializer,
)
from apps.system.usecases.system_usecase import SystemUseCase
from apps.system.usecases.automation_class_usecase import AutomationClassUseCase
from apps.system.usecases.vendor_product_usecase import VendorProductUseCase
from apps.objects.usecases.object_system_usecase import ObjectSystemUseCase
from apps.objects.api.serializers import ObjectSystemSerializer


class AutomationClassListView(APIView):
    """API списка классов автоматизации (только чтение)."""
    permission_classes = [AllowAny]

    def get(self, request):
        """Возвращает данные в ответе API."""
        usecase = AutomationClassUseCase()
        classes = usecase.list()
        serializer = AutomationClassSerializer(classes, many=True)
        return Response(serializer.data)


class VendorProductListCreateView(APIView):
    """API списка продуктов (GET) и создания продукта (POST)."""
    def get_permissions(self):
        """Права доступа: чтение — всем, изменение — аутентифицированным."""
        if self.request.method == "POST":
            return [IsAuthenticated()]
        return [AllowAny()]

    def get(self, request):
        """Возвращает данные в ответе API."""
        search = request.query_params.get("search")
        ordering = request.query_params.getlist("ordering") or None
        usecase = VendorProductUseCase()
        products = usecase.list(search=search, ordering=ordering)
        serializer = VendorProductSerializer(products, many=True)
        return Response(serializer.data)

    def post(self, request):
        """Создаёт ресурс (или привязывает объект) и возвращает представление."""
        serializer = VendorProductCreateUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        usecase = VendorProductUseCase()
        obj = usecase.create(**serializer.validated_data)
        return Response(VendorProductSerializer(obj).data, status=status.HTTP_201_CREATED)


class VendorProductDetailView(APIView):
    """API одного продукта: получение, обновление, удаление."""
    def get_permissions(self):
        """Права доступа: чтение — всем, изменение — аутентифицированным."""
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAuthenticated()]

    def get(self, request, pk):
        """Возвращает данные в ответе API."""
        usecase = VendorProductUseCase()
        obj = usecase.get(pk)
        return Response(VendorProductSerializer(obj).data)

    def patch(self, request, pk):
        """Частично обновляет ресурс переданными полями."""
        serializer = VendorProductCreateUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        usecase = VendorProductUseCase()
        obj = usecase.update(pk, **serializer.validated_data)
        return Response(VendorProductSerializer(obj).data)

    def delete(self, request, pk):
        """Удаляет ресурс."""
        usecase = VendorProductUseCase()
        usecase.delete(pk)
        return Response(status=status.HTTP_204_NO_CONTENT)


class SystemListCreateView(APIView):
    """API списка систем (GET) и создания системы (POST)."""
    def get_permissions(self):
        """Права доступа: чтение — всем, изменение — аутентифицированным."""
        if self.request.method == "POST":
            return [IsAuthenticated()]
        return [AllowAny()]

    def get(self, request):
        """Возвращает данные в ответе API."""
        system_class = request.query_params.get("system_class")
        search = request.query_params.get("search")
        obj = request.query_params.getlist("object") or None
        product = request.query_params.getlist("product") or None
        system_status = request.query_params.getlist("system_status") or None
        ordering = request.query_params.getlist("ordering") or None
        usecase = SystemUseCase()
        systems = usecase.list(
            system_class=system_class,
            search=search,
            obj=obj,
            product=product,
            system_status=system_status,
            ordering=ordering,
        )
        serializer = SystemListSerializer(systems, many=True)
        return Response(serializer.data)

    def post(self, request):
        """Создаёт ресурс (или привязывает объект) и возвращает представление."""
        serializer = SystemCreateUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        usecase = SystemUseCase()
        obj = usecase.create(user=request.user, **serializer.validated_data)
        return Response(
            SystemDetailSerializer(obj).data, status=status.HTTP_201_CREATED
        )


class SystemDetailView(APIView):
    """API одной системы: получение, обновление, удаление."""
    def get_permissions(self):
        """Права доступа: чтение — всем, изменение — аутентифицированным."""
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAuthenticated()]

    def get(self, request, pk):
        """Возвращает данные в ответе API."""
        usecase = SystemUseCase()
        obj = usecase.get(pk)
        serializer = SystemDetailSerializer(obj)
        return Response(serializer.data)

    def patch(self, request, pk):
        """Частично обновляет ресурс переданными полями."""
        serializer = SystemCreateUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        usecase = SystemUseCase()
        obj = usecase.update(pk, request.user, **serializer.validated_data)
        return Response(SystemDetailSerializer(obj).data)

    def delete(self, request, pk):
        """Удаляет ресурс."""
        usecase = SystemUseCase()
        usecase.delete(pk, request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class SystemAttachObjectView(APIView):
    """Привязать существующий объект к системе (создать связь ObjectSystem)."""

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        """Создаёт ресурс (или привязывает объект) и возвращает представление."""
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
