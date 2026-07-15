"""Тесты приложения пользователей: HTML-эндпоинты и REST API аутентификации."""
from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient


class UsersWebEndpointTests(TestCase):
    """Тесты HTML-эндпоинтов пользователей (вход, регистрация, профиль)."""
    def setUp(self):
        """Готовит тестовые данные перед каждым тестом."""
        self.password = "strong-password"
        self.user = User.objects.create_user(username="user", password=self.password)

    def test_login_page_is_available(self):
        """Страница входа открывается (200)."""
        response = self.client.get("/auth/login/")
        self.assertEqual(response.status_code, 200)

    def test_register_page_is_available(self):
        """Страница регистрации открывается (200)."""
        response = self.client.get("/auth/register/")
        self.assertEqual(response.status_code, 200)

    def test_register_endpoint_creates_user_and_redirects(self):
        """Регистрация создаёт пользователя и делает редирект."""
        response = self.client.post("/auth/register/", {
            "username": "new-user",
            "password": "pass1234",
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username="new-user").exists())

    def test_login_endpoint_logs_user_in_and_redirects(self):
        """Вход авторизует пользователя и делает редирект."""
        response = self.client.post("/auth/login/", {
            "username": self.user.username,
            "password": self.password,
        })
        self.assertEqual(response.status_code, 302)

    def test_profile_pages_require_authentication(self):
        """Страницы профиля требуют авторизации."""
        protected_urls = [
            "/auth/profile/",
            "/auth/profile/objects/",
            "/auth/profile/systems/",
            "/auth/profile/categories/",
        ]
        for url in protected_urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)
                self.assertIn("/auth/login/", response["Location"])

    def test_profile_pages_are_available_for_authenticated_user(self):
        """Страницы профиля доступны авторизованному пользователю."""
        self.client.force_login(self.user)
        protected_urls = [
            "/auth/profile/",
            "/auth/profile/objects/",
            "/auth/profile/systems/",
            "/auth/profile/categories/",
        ]
        for url in protected_urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)

    def test_logout_endpoint_redirects(self):
        """Выход делает редирект на страницу входа."""
        self.client.force_login(self.user)
        response = self.client.post("/auth/logout/")
        self.assertEqual(response.status_code, 302)


class UsersApiEndpointTests(TestCase):
    """Тесты REST API аутентификации (регистрация, вход)."""
    def setUp(self):
        """Готовит тестовые данные перед каждым тестом."""
        self.password = "strong-password"
        self.user = User.objects.create_user(username="api-user", password=self.password)
        self.api_client = APIClient()

    def test_register_api_returns_tokens(self):
        """API регистрации возвращает пару JWT-токенов."""
        response = self.api_client.post("/api/auth/register/", {
            "username": "api-new-user",
            "password": "pass1234",
        }, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_login_api_returns_tokens(self):
        """API входа возвращает пару JWT-токенов."""
        response = self.api_client.post("/api/auth/login/", {
            "username": self.user.username,
            "password": self.password,
        }, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
