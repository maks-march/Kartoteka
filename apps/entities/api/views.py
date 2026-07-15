"""REST API участников рынка."""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny

from rest_framework.exceptions import NotFound, ValidationError as DRFValidationError
from django.core.exceptions import ValidationError

from apps.entities.api.serializers import (
    EntitySerializer,
    EntityCreateUpdateSerializer,
    EngineeringProfileSerializer,
    EngineeringProfileWriteSerializer,
    FullCycleProfileSerializer,
    FullCycleProfileWriteSerializer,
    SupplierProfileSerializer,
    SupplierProductsWriteSerializer,
    SystemIntegratorProfileSerializer,
    SystemIntegratorProfileWriteSerializer,
    VendorProductsWriteSerializer,
)
from apps.entities.usecases.entity_usecase import EntityUseCase


class EntityListCreateView(APIView):
    """API списка участников (GET) и создания участника (POST)."""
    def get_permissions(self):
        """Права доступа: чтение — всем, изменение — аутентифицированным."""
        if self.request.method == "POST":
            return [IsAuthenticated()]
        return [AllowAny()]

    def get(self, request):
        """Возвращает данные участника(ов)/профиля в ответе API."""
        search = request.query_params.get("search")
        ordering = request.query_params.getlist("ordering") or None
        usecase = EntityUseCase()
        entities = usecase.list(search=search, ordering=ordering)
        serializer = EntitySerializer(entities, many=True)
        return Response(serializer.data)

    def post(self, request):
        """Создаёт участника и возвращает его представление."""
        serializer = EntityCreateUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        usecase = EntityUseCase()
        obj = usecase.create(**serializer.validated_data)
        return Response(EntitySerializer(obj).data, status=status.HTTP_201_CREATED)


class EntityDetailView(APIView):
    """API одного участника: получение, обновление, удаление."""
    def get_permissions(self):
        """Права доступа: чтение — всем, изменение — аутентифицированным."""
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAuthenticated()]

    def get(self, request, pk):
        """Возвращает данные участника(ов)/профиля в ответе API."""
        usecase = EntityUseCase()
        obj = usecase.get(pk)
        return Response(EntitySerializer(obj).data)

    def patch(self, request, pk):
        """Частично обновляет участника переданными полями."""
        serializer = EntityCreateUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        usecase = EntityUseCase()
        obj = usecase.update(pk, **serializer.validated_data)
        return Response(EntitySerializer(obj).data)

    def delete(self, request, pk):
        """Удаляет участника."""
        usecase = EntityUseCase()
        usecase.delete(pk)
        return Response(status=status.HTTP_204_NO_CONTENT)


class EngineeringProfileView(APIView):
    """Профиль инжиниринговой компании участника.

    GET  — чтение профиля (404, если участник не инжиниринговая компания).
    PUT  — сохранение полей профиля (region, вхожий объект, компетенции).
    """

    def get_permissions(self):
        """Права доступа: чтение — всем, изменение — аутентифицированным."""
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAuthenticated()]

    def get(self, request, pk):
        """Возвращает данные участника(ов)/профиля в ответе API."""
        entity = EntityUseCase().get(pk)
        profile = getattr(entity, "engineering_profile", None)
        if profile is None:
            raise NotFound("У участника нет профиля инжиниринговой компании")
        return Response(EngineeringProfileSerializer(profile).data)

    def put(self, request, pk):
        """Сохраняет профиль участника переданными данными."""
        usecase = EntityUseCase()
        entity = usecase.get(pk)
        if not entity.is_engineering_type:
            raise DRFValidationError(
                "Профиль доступен только для типа «Инжиниринговая компания»"
            )
        serializer = EngineeringProfileWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        competencies = [
            (c["system_class"], c["industry"]) for c in data.get("function_competencies", [])
        ]
        try:
            usecase.save_engineering_profile(
                entity,
                region=data.get("region", ""),
                resident_object_id=data.get("resident_object"),
                product_ids=data.get("product_competencies", []),
                competencies=competencies,
            )
        except ValidationError as e:
            raise DRFValidationError(str(e))
        entity = usecase.get(pk)
        return Response(EngineeringProfileSerializer(entity.engineering_profile).data)


class VendorProductsView(APIView):
    """Продукты вендора участника (привязка к VendorProfile).

    GET — id продуктов вендора (404, если участник не вендорского типа).
    PUT — задать список продуктов вендора.
    """

    def get_permissions(self):
        """Права доступа: чтение — всем, изменение — аутентифицированным."""
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAuthenticated()]

    def get(self, request, pk):
        """Возвращает данные участника(ов)/профиля в ответе API."""
        entity = EntityUseCase().get(pk)
        if not entity.is_vendor_type:
            raise NotFound("У участника нет профиля вендора")
        return Response({"product_ids": list(entity.products.values_list("id", flat=True))})

    def put(self, request, pk):
        """Сохраняет профиль участника переданными данными."""
        usecase = EntityUseCase()
        entity = usecase.get(pk)
        if not entity.is_vendor_type:
            raise DRFValidationError("Продукты доступны только для вендорских типов")
        serializer = VendorProductsWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            usecase.save_vendor_products(
                entity, product_ids=serializer.validated_data["product_ids"]
            )
        except ValidationError as e:
            raise DRFValidationError(str(e))
        entity = usecase.get(pk)
        return Response({"product_ids": list(entity.products.values_list("id", flat=True))})


class SupplierProductsView(APIView):
    """Поставляемые продукты участника (профиль поставщика).

    GET — профиль поставщика (404, если участник не поставщикского типа).
    PUT — задать список поставляемых продуктов.
    """

    def get_permissions(self):
        """Права доступа: чтение — всем, изменение — аутентифицированным."""
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAuthenticated()]

    def get(self, request, pk):
        """Возвращает данные участника(ов)/профиля в ответе API."""
        entity = EntityUseCase().get(pk)
        profile = getattr(entity, "supplier_profile", None)
        if profile is None:
            raise NotFound("У участника нет профиля поставщика")
        return Response(SupplierProfileSerializer(profile).data)

    def put(self, request, pk):
        """Сохраняет профиль участника переданными данными."""
        usecase = EntityUseCase()
        entity = usecase.get(pk)
        if not entity.is_supplier_type:
            raise DRFValidationError("Профиль доступен только для типа «Поставщик»")
        serializer = SupplierProductsWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            usecase.save_supplier_products(
                entity, product_ids=serializer.validated_data["product_ids"]
            )
        except ValidationError as e:
            raise DRFValidationError(str(e))
        entity = usecase.get(pk)
        return Response(SupplierProfileSerializer(entity.supplier_profile).data)


class SystemIntegratorProfileView(APIView):
    """Профиль системного интегратора участника.

    GET — профиль (404, если участник не системный интегратор).
    PUT — управляющая компания + вендоры-партнёры.
    """

    def get_permissions(self):
        """Права доступа: чтение — всем, изменение — аутентифицированным."""
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAuthenticated()]

    def get(self, request, pk):
        """Возвращает данные участника(ов)/профиля в ответе API."""
        entity = EntityUseCase().get(pk)
        profile = getattr(entity, "system_integrator_profile", None)
        if profile is None:
            raise NotFound("У участника нет профиля системного интегратора")
        return Response(SystemIntegratorProfileSerializer(profile).data)

    def put(self, request, pk):
        """Сохраняет профиль участника переданными данными."""
        usecase = EntityUseCase()
        entity = usecase.get(pk)
        if not entity.is_system_integrator_type:
            raise DRFValidationError(
                "Профиль доступен только для типа «Системный интегратор»"
            )
        serializer = SystemIntegratorProfileWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            usecase.save_system_integrator_profile(
                entity,
                managing_owner_id=data.get("managing_owner"),
                vendor_partner_ids=data.get("vendor_partner_ids", []),
            )
        except ValidationError as e:
            raise DRFValidationError(str(e))
        entity = usecase.get(pk)
        return Response(
            SystemIntegratorProfileSerializer(entity.system_integrator_profile).data
        )


class FullCycleProfileView(APIView):
    """Dedicated профиль вендора полного цикла участника.

    GET — профиль (404, если участник не вендор полного цикла).
    PUT — region + вхожий объект + компетенции (продукты и функции).
    """

    def get_permissions(self):
        """Права доступа: чтение — всем, изменение — аутентифицированным."""
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAuthenticated()]

    def get(self, request, pk):
        """Возвращает данные участника(ов)/профиля в ответе API."""
        entity = EntityUseCase().get(pk)
        profile = getattr(entity, "full_cycle_profile", None)
        if profile is None:
            raise NotFound("У участника нет профиля вендора полного цикла")
        return Response(FullCycleProfileSerializer(profile).data)

    def put(self, request, pk):
        """Сохраняет профиль участника переданными данными."""
        usecase = EntityUseCase()
        entity = usecase.get(pk)
        if entity.entity_type != "full_cycle_vendor":
            raise DRFValidationError(
                "Профиль доступен только для типа «Вендор полного цикла»"
            )
        serializer = FullCycleProfileWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        competencies = [
            (c["system_class"], c["industry"]) for c in data.get("function_competencies", [])
        ]
        try:
            usecase.save_full_cycle_profile(
                entity,
                region=data.get("region", ""),
                resident_object_id=data.get("resident_object"),
                product_ids=data.get("product_competencies", []),
                competencies=competencies,
            )
        except ValidationError as e:
            raise DRFValidationError(str(e))
        entity = usecase.get(pk)
        return Response(FullCycleProfileSerializer(entity.full_cycle_profile).data)
