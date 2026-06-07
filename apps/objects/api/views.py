"""API View-ы для объектов (ViewSet)."""

from rest_framework import viewsets, mixins, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from objects_app.repository.impl import DjangoObjectRepository
from objects_app.usecase.get_object import GetObjectByIdUseCase, ListObjectsUseCase
from objects_app.usecase.create_object import CreateObjectUseCase
from objects_app.usecase.update_object import UpdateObjectUseCase
from objects_app.usecase.delete_object import DeleteObjectUseCase
from objects_app.api.serializers import ObjectInputSerializer, ObjectOutputSerializer
from categories.repository.impl import DjangoCategoryRepository


class ObjectViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """REST API для объектов."""

    serializer_class = ObjectOutputSerializer
    permission_classes = [AllowAny]

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return ObjectInputSerializer
        return ObjectOutputSerializer

    def list(self, request, *args, **kwargs):
        level = request.query_params.get("level")
        category_id = request.query_params.get("category_id")
        search = request.query_params.get("search")

        usecase = ListObjectsUseCase(object_repo=DjangoObjectRepository())
        entities = usecase.execute(
            level=int(level) if level else None,
            category_id=int(category_id) if category_id else None,
            search=search,
        )

        serializer = ObjectOutputSerializer(entities, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        usecase = GetObjectByIdUseCase(object_repo=DjangoObjectRepository())
        entity = usecase.execute(int(pk))

        serializer = ObjectOutputSerializer(entity)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = ObjectInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        usecase = CreateObjectUseCase(
            object_repo=DjangoObjectRepository(),
            category_repo=DjangoCategoryRepository(),
        )
        entity = usecase.execute(
            name=serializer.validated_data["name"],
            level=serializer.validated_data["level"],
            category_id=serializer.validated_data["category_id"],
        )

        output = ObjectOutputSerializer(entity)
        return Response(output.data, status=status.HTTP_201_CREATED)

    def update(self, request, pk=None):
        serializer = ObjectInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        usecase = UpdateObjectUseCase(
            object_repo=DjangoObjectRepository(),
            category_repo=DjangoCategoryRepository(),
        )
        entity = usecase.execute(
            obj_id=int(pk),
            name=serializer.validated_data["name"],
            level=serializer.validated_data["level"],
            category_id=serializer.validated_data["category_id"],
        )

        output = ObjectOutputSerializer(entity)
        return Response(output.data)

    def destroy(self, request, pk=None):
        usecase = DeleteObjectUseCase(object_repo=DjangoObjectRepository())
        usecase.execute(int(pk))
        return Response(status=status.HTTP_204_NO_CONTENT)
