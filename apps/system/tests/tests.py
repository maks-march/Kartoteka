from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from apps.categories.models import Category
from apps.objects.models import Object, ObjectSystem
from apps.system.models import AutomatedSystem, AutomationClass


class SystemEndpointTestMixin:
    def create_base_data(self):
        self.user = User.objects.create_user(username="user", password="password")
        self.automation_class = AutomationClass.objects.create(
            level=2,
            system_class="SCADA",
            description="Диспетчеризация",
        )
        self.system = AutomatedSystem.objects.create(
            autosystem_name="АСУ ТП",
            system_class=self.automation_class,
            creator_id=self.user,
        )
        self.category = Category.objects.create(name="Площадка", level=1, creator_id=self.user)
        self.object = Object.objects.create(
            name="Завод",
            level=1,
            category=self.category,
            creator_id=self.user,
        )


class SystemWebEndpointTests(SystemEndpointTestMixin, TestCase):
    def setUp(self):
        self.create_base_data()

    def test_system_list_page_is_available(self):
        response = self.client.get("/system/")
        self.assertEqual(response.status_code, 200)

    def test_system_list_supports_filters(self):
        response = self.client.get("/system/", {
            "system_class": str(self.automation_class.pk),
            "search": "асу",
        })
        self.assertEqual(response.status_code, 200)

    def test_system_detail_page_is_available(self):
        response = self.client.get(f"/system/{self.system.pk}/")
        self.assertEqual(response.status_code, 200)

    def test_system_create_page_requires_authentication(self):
        response = self.client.get("/system/create/")
        self.assertEqual(response.status_code, 302)

    def test_authenticated_system_crud_and_attach_object_endpoints(self):
        self.client.force_login(self.user)

        response = self.client.get("/system/create/")
        self.assertEqual(response.status_code, 200)

        response = self.client.post("/system/create/", {
            "autosystem_name": "MES",
            "system_class": str(self.automation_class.pk),
        })
        self.assertEqual(response.status_code, 302)
        created = AutomatedSystem.objects.get(autosystem_name="MES")

        response = self.client.get(f"/system/{created.pk}/edit/")
        self.assertEqual(response.status_code, 200)

        response = self.client.post(f"/system/{created.pk}/edit/", {
            "autosystem_name": "MES 2",
            "system_class": str(self.automation_class.pk),
        })
        self.assertEqual(response.status_code, 302)
        created.refresh_from_db()
        self.assertEqual(created.autosystem_name, "MES 2")

        response = self.client.get(f"/system/{created.pk}/attach-object/")
        self.assertEqual(response.status_code, 200)

        response = self.client.post(f"/system/{created.pk}/attach-object/", {
            "object": str(self.object.pk),
            "status": "active",
            "implementation_date": "2026-01-01",
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(ObjectSystem.objects.filter(object=self.object, system=created).exists())

        response = self.client.post(f"/system/{created.pk}/delete/")
        self.assertEqual(response.status_code, 302)
        self.assertFalse(AutomatedSystem.objects.filter(pk=created.pk).exists())


class SystemApiEndpointTests(SystemEndpointTestMixin, TestCase):
    def setUp(self):
        self.create_base_data()
        self.api_client = APIClient()

    def test_system_api_list_detail_and_classes_are_public(self):
        response = self.api_client.get("/api/system/classes/")
        self.assertEqual(response.status_code, 200)

        response = self.api_client.get("/api/system/", {
            "system_class": str(self.automation_class.pk),
            "search": "асу",
        })
        self.assertEqual(response.status_code, 200)

        response = self.api_client.get(f"/api/system/{self.system.pk}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], self.system.pk)

    def test_system_api_create_requires_authentication(self):
        response = self.api_client.post("/api/system/", {
            "autosystem_name": "API MES",
            "system_class": self.automation_class.pk,
        }, format="json")
        self.assertIn(response.status_code, (401, 403))

    def test_authenticated_system_api_crud(self):
        self.api_client.force_authenticate(user=self.user)

        response = self.api_client.post("/api/system/", {
            "autosystem_name": "API MES",
            "system_class": self.automation_class.pk,
        }, format="json")
        self.assertEqual(response.status_code, 201)
        system_id = response.data["id"]

        response = self.api_client.patch(f"/api/system/{system_id}/", {
            "autosystem_name": "API MES 2",
            "system_class": self.automation_class.pk,
        }, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["autosystem_name"], "API MES 2")

        response = self.api_client.delete(f"/api/system/{system_id}/")
        self.assertEqual(response.status_code, 204)
        self.assertFalse(AutomatedSystem.objects.filter(pk=system_id).exists())

    def test_system_api_attach_object_requires_authentication(self):
        response = self.api_client.post(
            f"/api/system/{self.system.pk}/attach-object/",
            {"object": self.object.pk},
            format="json",
        )
        self.assertIn(response.status_code, (401, 403))

    def test_authenticated_system_api_attach_object(self):
        self.api_client.force_authenticate(user=self.user)
        response = self.api_client.post(
            f"/api/system/{self.system.pk}/attach-object/",
            {
                "object": self.object.pk,
                "status": "active",
                "implementation_date": "2026-01-01",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["object"], self.object.pk)
        self.assertEqual(response.data["system"], self.system.pk)
        self.assertEqual(response.data["status"], "active")
        self.assertTrue(
            ObjectSystem.objects.filter(object=self.object, system=self.system).exists()
        )

    def test_system_api_attach_object_duplicate_is_rejected(self):
        self.api_client.force_authenticate(user=self.user)
        ObjectSystem.objects.create(object=self.object, system=self.system, status="planned")
        response = self.api_client.post(
            f"/api/system/{self.system.pk}/attach-object/",
            {"object": self.object.pk},
            format="json",
        )
        self.assertIn(response.status_code, (400, 422))

    def test_system_api_attach_object_unknown_system_returns_404(self):
        self.api_client.force_authenticate(user=self.user)
        response = self.api_client.post(
            "/api/system/999999/attach-object/",
            {"object": self.object.pk},
            format="json",
        )
        self.assertEqual(response.status_code, 404)
