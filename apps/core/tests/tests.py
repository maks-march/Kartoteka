"""Тесты общего приложения (доступность главной страницы)."""
from django.test import TestCase


class CoreEndpointTests(TestCase):
    """Тесты HTML-эндпоинтов общего приложения."""
    def test_hub_page_is_available(self):
        """Главная страница-хаб открывается (200)."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
