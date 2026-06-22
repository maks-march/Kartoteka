from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from apps.categories.models import Category


class CategoriesWebEndpointTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="user", password="password")
        self.category = Category.objects.create(
            name="Производство",
            level=1,
            creator_id=self.user,
        )

    def test_category_list_page_is_available(self):
        response = self.client.get("/categories/")
        self.assertEqual(response.status_code, 200)

    def test_category_list_supports_filters(self):
        response = self.client.get("/categories/", {"level": "1", "search": "производ"})
        self.assertEqual(response.status_code, 200)

    def test_category_detail_page_is_available(self):
        response = self.client.get(f"/categories/{self.category.pk}/")
        self.assertEqual(response.status_code, 200)

    def test_category_create_page_requires_authentication(self):
        response = self.client.get("/categories/create/")
        self.assertEqual(response.status_code, 302)

    def test_authenticated_category_crud_endpoints(self):
        self.client.force_login(self.user)

        response = self.client.get("/categories/create/")
        self.assertEqual(response.status_code, 200)

        response = self.client.post("/categories/create/", {
            "name": "Склад",
            "level": "2",
        })
        self.assertEqual(response.status_code, 302)
        created = Category.objects.get(name="Склад")

        response = self.client.get(f"/categories/{created.pk}/edit/")
        self.assertEqual(response.status_code, 200)

        response = self.client.post(f"/categories/{created.pk}/edit/", {
            "name": "Склад готовой продукции",
            "level": "2",
        })
        self.assertEqual(response.status_code, 302)
        created.refresh_from_db()
        self.assertEqual(created.name, "Склад готовой продукции")

        response = self.client.post(f"/categories/{created.pk}/delete/")
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Category.objects.filter(pk=created.pk).exists())


class CategoriesApiEndpointTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="api-user", password="password")
        self.category = Category.objects.create(name="Цех", level=1, creator_id=self.user)
        self.api_client = APIClient()

    def test_category_api_list_and_detail_are_public(self):
        response = self.api_client.get("/api/categories/categories/")
        self.assertEqual(response.status_code, 200)

        response = self.api_client.get(f"/api/categories/categories/{self.category.pk}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], self.category.pk)

    def test_category_api_create_requires_authentication(self):
        response = self.api_client.post("/api/categories/categories/", {
            "name": "Линия",
            "level": 2,
        }, format="json")
        self.assertIn(response.status_code, (401, 403))

    def test_authenticated_category_api_crud(self):
        self.api_client.force_authenticate(user=self.user)

        response = self.api_client.post("/api/categories/categories/", {
            "name": "Линия",
            "level": 2,
        }, format="json")
        self.assertEqual(response.status_code, 201)
        category_id = response.data["id"]

        response = self.api_client.patch(f"/api/categories/categories/{category_id}/", {
            "name": "Линия розлива",
            "level": 2,
        }, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["name"], "Линия розлива")

        response = self.api_client.delete(f"/api/categories/categories/{category_id}/")
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Category.objects.filter(pk=category_id).exists())
