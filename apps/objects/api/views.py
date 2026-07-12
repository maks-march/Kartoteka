"""REST API объектов производства и связей «система на объекте»."""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny

from apps.objects.api.serializers import (
    ObjectListSerializer,
    ObjectDetailSerializer,
    ObjectCreateSerializer,
    ObjectUpdateSerializer,
    ObjectSystemSerializer,
    ObjectSystemCreateSerializer,
    ObjectSystemUpdateSerializer,
)
from apps.objects.usecases.object_usecase import ObjectUseCase
from apps.objects.usecases.object_system_usecase import ObjectSystemUseCase


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
        owner_entity = request.query_params.getlist("owner_entity") or None
        ordering = request.query_params.getlist("ordering") or None
        usecase = ObjectUseCase()
        objects = usecase.list(
            level=level,
            search=search,
            category=category,
            system=system,
            owner_entity=owner_entity,
            ordering=ordering,
        )
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


class ObjectSystemListCreateView(APIView):
    """Связи «система на объекте».

    GET  — список связей; можно отфильтровать по ?object=<id> или ?system=<id>.
    POST — привязать систему к объекту (attach).
    """

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated()]
        return [AllowAny()]

    def get(self, request):
        object_id = request.query_params.get("object")
        system_id = request.query_params.get("system")
        os_usecase = ObjectSystemUseCase()
        object_usecase = ObjectUseCase()

        if object_id:
            obj = object_usecase.get(object_id)
            links = os_usecase.list_for_object(obj)
        elif system_id:
            from apps.system.usecases.system_usecase import SystemUseCase
            system = SystemUseCase().get(system_id)
            links = os_usecase.list_for_system(system)
        else:
            from apps.objects.models import ObjectSystem
            links = ObjectSystem.objects.select_related(
                "object", "system", "integrator", "implementor"
            ).all()

        serializer = ObjectSystemSerializer(links, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = ObjectSystemCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        os_usecase = ObjectSystemUseCase()
        link = os_usecase.attach(
            object_pk=data.pop("object"),
            system_pk=data.pop("system"),
            **data,
        )
        return Response(
            ObjectSystemSerializer(link).data, status=status.HTTP_201_CREATED
        )


class ObjectSystemDetailView(APIView):
    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAuthenticated()]

    def get(self, request, pk):
        os_usecase = ObjectSystemUseCase()
        link = os_usecase.get(pk)
        return Response(ObjectSystemSerializer(link).data)

    def patch(self, request, pk):
        serializer = ObjectSystemUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        os_usecase = ObjectSystemUseCase()
        link = os_usecase.update(
            pk,
            object_pk=data.pop("object", None),
            system_pk=data.pop("system", None),
            **data,
        )
        return Response(ObjectSystemSerializer(link).data)

    def delete(self, request, pk):
        os_usecase = ObjectSystemUseCase()
        os_usecase.detach(pk)
        return Response(status=status.HTTP_204_NO_CONTENT)
