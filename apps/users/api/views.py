"""API View-ы для users."""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from users.repository.impl import DjangoUserRepository
from users.usecase.register_user import RegisterUserUseCase
from users.usecase.authenticate_user import AuthenticateUserUseCase
from users.api.serializers import (
    RegisterInputSerializer,
    LoginInputSerializer,
    UserOutputSerializer,
    TokenOutputSerializer,
)

from rest_framework_simplejwt.tokens import RefreshToken
from common.exceptions import AuthenticationError
from users.domain.models import CustomUser


class RegisterAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        usecase = RegisterUserUseCase(user_repo=DjangoUserRepository())
        user_entity = usecase.execute(
            username=serializer.validated_data["username"],
            email=serializer.validated_data["email"],
            password=serializer.validated_data["password"],
        )

        # Выдаём токены сразу после регистрации (получаем DB-объект)
        db_user = CustomUser.objects.get(pk=user_entity.id)
        refresh = RefreshToken.for_user(db_user)
        tokens = {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }

        output = UserOutputSerializer(user_entity).data
        return Response(
            {"user": output, "tokens": tokens},
            status=status.HTTP_201_CREATED,
        )


class LoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        usecase = AuthenticateUserUseCase(user_repo=DjangoUserRepository())
        user_data = usecase.execute(
            username=serializer.validated_data["username"],
            password=serializer.validated_data["password"],
        )

        # Генерируем JWT-токены
        db_user = CustomUser.objects.get(pk=user_data["id"])
        refresh = RefreshToken.for_user(db_user)

        tokens = {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }

        return Response(
            {"user": user_data, "tokens": tokens},
            status=status.HTTP_200_OK,
        )
