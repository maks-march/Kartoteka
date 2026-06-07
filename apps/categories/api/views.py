"""API View-ы для категорий (ViewSet)."""

from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, AllowAny

from categories.repository.impl import DjangoCategoryRepository
from categories.usecase.create_category import CreateCategoryUseCase
from categories.usecase.update_category import UpdateCategoryUseCase
from categories.usecase.delete_category import DeleteCategoryUseCase
from categories.usecase.get_category import (
    GetCategoryByIdUseCase,
    ListCategoriesUseCase,
    GetCategoryObjectCountUseCase,
)
from categories.api.serializers import CategoryInputSerializer, CategoryOutputSerializer
from objects_app.repository.impl import DjangoObjectRepository
from objects_app.usecase.get_object import ListObjectsUseCase
from objects_app.api.serializers import ObjectOutputSerializer


class CategoryViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """REST API для категорий."""
    serializer_class = CategoryOutputSerializer
    permission_classes = [AllowAny]  # можно заменить на IsAuthenticated для write

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return CategoryInputSerializer
        return CategoryOutputSerializer

    def list(self, request, *args, **kwargs):
        level = request.query_params.get("level")
        usecase = ListCategoriesUseCase(category_repo=DjangoCategoryRepository())
        entities = usecase.execute(level=int(level) if level else None)

        # Добавляем счётчик объектов
        count_usecase = GetCategoryObjectCountUseCase(category_repo=DjangoCategoryRepository())
        output_data = []
        for entity in entities:
            count = count_usecase.execute(entity.id)
            output_data.append({
                "id": entity.id,
                "name": entity.name,
                "level": entity.level,
                "objects_count": count,
            })

        serializer = self.get_serializer_class()(output_data, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        usecase = GetCategoryByIdUseCase(category_repo=DjangoCategoryRepository())
        entity = usecase.execute(int(pk))

        count_usecase = GetCategoryObjectCountUseCase(category_repo=DjangoCategoryRepository())
        count = count_usecase.execute(entity.id)

        serializer = CategoryOutputSerializer({
            "id": entity.id,
            "name": entity.name,
            "level": entity.level,
            "objects_count": count,
        })
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = CategoryInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        usecase = CreateCategoryUseCase(category_repo=DjangoCategoryRepository())
        entity = usecase.execute(
            name=serializer.validated_data["name"],
            level=serializer.validated_data["level"],
        )

        output = CategoryOutputSerializer({
            "id": entity.id,
            "name": entity.name,
            "level": entity.level,
            "objects_count": 0,
        })
        return Response(output.data, status=status.HTTP_201_CREATED)

    def update(self, request, pk=None):
        serializer = CategoryInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        usecase = UpdateCategoryUseCase(category_repo=DjangoCategoryRepository())
        entity = usecase.execute(
            category_id=int(pk),
            name=serializer.validated_data["name"],
            level=serializer.validated_data["level"],
        )

        count_usecase = GetCategoryObjectCountUseCase(category_repo=DjangoCategoryRepository())
        count = count_usecase.execute(entity.id)

        output = CategoryOutputSerializer({
            "id": entity.id,
            "name": entity.name,
            "level": entity.level,
            "objects_count": count,
        })
        return Response(output.data)

    def destroy(self, request, pk=None):
        usecase = DeleteCategoryUseCase(category_repo=DjangoCategoryRepository())
        usecase.execute(int(pk))
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["get"])
    def objects(self, request, pk=None):
        """Получить все объекты данной категории."""
        # Проверяем что категория существует
        usecase = GetCategoryByIdUseCase(category_repo=DjangoCategoryRepository())
        usecase.execute(int(pk))

        # Получаем объекты
        obj_usecase = ListObjectsUseCase(object_repo=DjangoObjectRepository())
        objects = obj_usecase.execute(category_id=int(pk))

        serializer = ObjectOutputSerializer(objects, many=True)
        return Response(serializer.data)
