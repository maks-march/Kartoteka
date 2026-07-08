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


class EngineeringProfileView(APIView):
    """Профиль инжиниринговой компании участника.

    GET  — чтение профиля (404, если участник не инжиниринговая компания).
    PUT  — сохранение полей профиля (region, вхожий объект, компетенции).
    """

    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAuthenticated()]

    def get(self, request, pk):
        entity = EntityUseCase().get(pk)
        profile = getattr(entity, "engineering_profile", None)
        if profile is None:
            raise NotFound("У участника нет профиля инжиниринговой компании")
        return Response(EngineeringProfileSerializer(profile).data)

    def put(self, request, pk):
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
