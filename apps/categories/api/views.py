from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny

from apps.categories.api.serializers import CategorySerializer, CategoryCreateUpdateSerializer
from apps.categories.usecases.category_usecase import CategoryUseCase


class CategoryListCreateView(APIView):
    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated()]
        return [AllowAny()]

    def get(self, request):
        level = request.query_params.get("level")
        search = request.query_params.get("search")
        usecase = CategoryUseCase()
        categories = usecase.list(level=level, search=search)
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = CategoryCreateUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        usecase = CategoryUseCase()
        obj = usecase.create(**serializer.validated_data)
        return Response(
            CategorySerializer(obj).data, status=status.HTTP_201_CREATED
        )


class CategoryDetailView(APIView):
    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAuthenticated()]

    def get(self, request, pk):
        usecase = CategoryUseCase()
        obj = usecase.get(pk)
        serializer = CategorySerializer(obj)
        return Response(serializer.data)

    def patch(self, request, pk):
        serializer = CategoryCreateUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        usecase = CategoryUseCase()
        obj = usecase.update(pk, **serializer.validated_data)
        return Response(CategorySerializer(obj).data)

    def delete(self, request, pk):
        usecase = CategoryUseCase()
        usecase.delete(pk)
        return Response(status=status.HTTP_204_NO_CONTENT)
