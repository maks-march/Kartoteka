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


class SystemNewFieldsTests(SystemEndpointTestMixin, TestCase):
    """Новые поля системы: идентификация, состояние, жизненный цикл, JSON-данные."""

    def setUp(self):
        self.create_base_data()
        self.api_client = APIClient()

    # ---------- usecase / web ----------
    def test_web_create_persists_new_fields(self):
        self.client.force_login(self.user)
        response = self.client.post("/system/create/", {
            "autosystem_name": "PCS 7 Full",
            "autosystem_short_name": "PCS7",
            "system_class": str(self.automation_class.pk),
            "version": "V9.1",
            "system_status": "pilot",
            "product_type": "hardware",
            "article": "ART-777",
            "notes": "Примечание",
            "release_year": "2021-05-20",
            "end_of_support": "2030-12-31",
            "technical_specs": '{"cpu": "x86"}',
            "modules": '["m1", "m2"]',
            "interfaces": "",
        })
        self.assertEqual(response.status_code, 302)
        s = AutomatedSystem.objects.get(autosystem_name="PCS 7 Full")
        self.assertEqual(s.autosystem_short_name, "PCS7")
        self.assertEqual(s.version, "V9.1")
        self.assertEqual(s.system_status, "pilot")
        self.assertEqual(s.product_type, "hardware")
        self.assertEqual(s.article, "ART-777")
        self.assertEqual(s.technical_specs, {"cpu": "x86"})
        self.assertEqual(s.modules, ["m1", "m2"])
        self.assertIsNone(s.interfaces)

    def test_status_defaults_to_active(self):
        from apps.system.usecases.system_usecase import SystemUseCase
        s = SystemUseCase().create(
            user=self.user,
            autosystem_name="Default",
            system_class=self.automation_class.pk,
        )
        self.assertEqual(s.system_status, "active")
        self.assertEqual(s.status_tag_class, "tag-ok")

    def test_empty_article_stored_as_null_allows_multiple(self):
        from apps.system.usecases.system_usecase import SystemUseCase
        uc = SystemUseCase()
        a = uc.create(user=self.user, autosystem_name="A", system_class=self.automation_class.pk, article="")
        b = uc.create(user=self.user, autosystem_name="B", system_class=self.automation_class.pk, article="")
        self.assertIsNone(a.article)
        self.assertIsNone(b.article)

    def test_web_create_invalid_json_shows_error(self):
        self.client.force_login(self.user)
        response = self.client.post("/system/create/", {
            "autosystem_name": "BadJSON",
            "system_class": str(self.automation_class.pk),
            "technical_specs": "{не json}",
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn("корректным JSON", response.content.decode())
        self.assertFalse(AutomatedSystem.objects.filter(autosystem_name="BadJSON").exists())

    def test_status_tag_class_mapping(self):
        s = AutomatedSystem(autosystem_name="x", system_class=self.automation_class, system_status="unsupported")
        self.assertEqual(s.status_tag_class, "tag-danger")

    # ---------- API ----------
    def test_api_create_with_new_fields(self):
        self.api_client.force_authenticate(user=self.user)
        response = self.api_client.post("/api/system/", {
            "autosystem_name": "API Sys",
            "autosystem_short_name": "AS",
            "system_class": self.automation_class.pk,
            "version": "2.0",
            "system_status": "implementing",
            "product_type": "service",
            "technical_specs": {"ram": "16GB"},
            "modules": ["x"],
        }, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["autosystem_short_name"], "AS")
        self.assertEqual(response.data["version"], "2.0")
        self.assertEqual(response.data["system_status"], "implementing")
        self.assertEqual(response.data["product_type"], "service")
        self.assertEqual(response.data["technical_specs"], {"ram": "16GB"})
        self.assertEqual(response.data["modules"], ["x"])

    def test_api_detail_exposes_new_fields(self):
        s = AutomatedSystem.objects.create(
            autosystem_name="Detail Sys",
            system_class=self.automation_class,
            version="3.3",
            system_status="active",
            product_type="software",
            interfaces=["OPC UA"],
            creator_id=self.user,
        )
        response = self.api_client.get(f"/api/system/{s.pk}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["version"], "3.3")
        self.assertEqual(response.data["interfaces"], ["OPC UA"])
        self.assertEqual(response.data["status_display"], "В эксплуатации")
