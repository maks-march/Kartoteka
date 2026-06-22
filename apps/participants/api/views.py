from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny

from apps.participants.api.serializers import (
    ParticipantSerializer,
    ParticipantCreateUpdateSerializer,
)
from apps.participants.usecases.participant_usecase import ParticipantUseCase


class ParticipantListCreateView(APIView):
    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated()]
        return [AllowAny()]

    def get(self, request):
        search = request.query_params.get("search")
        usecase = ParticipantUseCase()
        participants = usecase.list(search=search)
        serializer = ParticipantSerializer(participants, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = ParticipantCreateUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        usecase = ParticipantUseCase()
        obj = usecase.create(**serializer.validated_data)
        return Response(ParticipantSerializer(obj).data, status=status.HTTP_201_CREATED)


class ParticipantDetailView(APIView):
    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAuthenticated()]

    def get(self, request, pk):
        usecase = ParticipantUseCase()
        obj = usecase.get(pk)
        return Response(ParticipantSerializer(obj).data)

    def patch(self, request, pk):
        serializer = ParticipantCreateUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        usecase = ParticipantUseCase()
        obj = usecase.update(pk, **serializer.validated_data)
        return Response(ParticipantSerializer(obj).data)

    def delete(self, request, pk):
        usecase = ParticipantUseCase()
        usecase.delete(pk)
        return Response(status=status.HTTP_204_NO_CONTENT)
