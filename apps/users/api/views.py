"""REST API аутентификации: регистрация и вход с выдачей JWT."""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.api.serializers import RegisterSerializer, LoginSerializer
from apps.users.usecases.usecase import AuthUseCase


class RegisterView(APIView):
    """API регистрации: создаёт пользователя и возвращает пару JWT."""
    permission_classes = [AllowAny]

    def post(self, request):
        """Обрабатывает POST-запрос: валидирует данные и возвращает JWT."""
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        usecase = AuthUseCase()
        try:
            user = usecase.register(**serializer.validated_data)
        except Exception as e:
            raise DRFValidationError({"detail": str(e)})

        refresh = RefreshToken.for_user(user)
        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """API входа: проверяет учётные данные и возвращает пару JWT."""
    permission_classes = [AllowAny]

    def post(self, request):
        """Обрабатывает POST-запрос: валидирует данные и возвращает JWT."""
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        usecase = AuthUseCase()
        try:
            user = usecase.login(**serializer.validated_data)
        except Exception as e:
            raise DRFValidationError({"detail": str(e)})

        refresh = RefreshToken.for_user(user)
        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        })
