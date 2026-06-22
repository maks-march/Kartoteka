from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from apps.categories.models import Category
from apps.objects.models import Object, ObjectSystem
from apps.owners.models import OwnerEntity
from apps.system.models import AutomatedSystem, AutomationClass


class ObjectsEndpointTestMixin:
    def create_base_data(self):
        self.user = User.objects.create_user(username="user", password="password")
        self.category_l1 = Category.objects.create(name="Площадка", level=1, creator_id=self.user)
        self.category_l2 = Category.objects.create(name="Цех", level=2, creator_id=self.user)
        self.owner_entity = OwnerEntity.objects.create(owner_name="ООО Ромашка")
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
        self.second_system = AutomatedSystem.objects.create(
            autosystem_name="MES",
            system_class=self.automation_class,
            creator_id=self.user,
        )
        self.object = Object.objects.create(
            name="Завод",
            level=1,
            category=self.category_l1,
            owner_entity=self.owner_entity,
            creator_id=self.user,
        )
        self.child = Object.objects.create(
            name="Цех 1",
            level=2,
            parent=self.object,
            category=self.category_l2,
            owner_entity=self.owner_entity,
            creator_id=self.user,
        )


class ObjectsWebEndpointTests(ObjectsEndpointTestMixin, TestCase):
    def setUp(self):
        self.create_base_data()

    def test_object_list_page_is_available(self):
        response = self.client.get("/objects/")
        self.assertEqual(response.status_code, 200)

    def test_object_list_supports_filters(self):
        response = self.client.get("/objects/", {
            "level": "1",
            "search": "завод",
            "category": str(self.category_l1.pk),
            "owner_entity": str(self.owner_entity.pk),
        })
        self.assertEqual(response.status_code, 200)

    def test_object_detail_page_is_available(self):
        response = self.client.get(f"/objects/{self.object.pk}/")
        self.assertEqual(response.status_code, 200)

    def test_object_create_page_requires_authentication(self):
        response = self.client.get("/objects/create/")
        self.assertEqual(response.status_code, 302)

    def test_authenticated_object_create_and_edit_endpoints(self):
        self.client.force_login(self.user)

        response = self.client.get("/objects/create/")
        self.assertEqual(response.status_code, 200)

        response = self.client.post("/objects/create/", {
            "name": "Новый завод",
            "level": "1",
            "parent": "",
            "category": str(self.category_l1.pk),
            "owner_entity": str(self.owner_entity.pk),
        })
        self.assertEqual(response.status_code, 302)
        created = Object.objects.get(name="Новый завод")
        self.assertEqual(created.owner_entity_id, self.owner_entity.pk)

        response = self.client.get(f"/objects/{created.pk}/edit/")
        self.assertEqual(response.status_code, 200)

        response = self.client.post(f"/objects/{created.pk}/edit/", {
            "name": "Новый завод 2",
            "level": "1",
            "parent": "",
            "category": str(self.category_l1.pk),
            "owner_entity": str(self.owner_entity.pk),
        })
        self.assertEqual(response.status_code, 302)
        created.refresh_from_db()
        self.assertEqual(created.name, "Новый завод 2")

    def test_authenticated_object_add_child_endpoint(self):
        self.client.force_login(self.user)

        response = self.client.get(f"/objects/{self.object.pk}/add-child/")
        self.assertEqual(response.status_code, 200)

        response = self.client.post(f"/objects/{self.object.pk}/add-child/", {
            "mode": "create",
            "name": "Цех 2",
            "level": "2",
            "category": str(self.category_l2.pk),
            "owner_entity": str(self.owner_entity.pk),
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Object.objects.filter(name="Цех 2", parent=self.object).exists())

    def test_authenticated_object_system_attach_edit_delete_endpoints(self):
        self.client.force_login(self.user)

        response = self.client.get(f"/objects/{self.object.pk}/attach-system/")
        self.assertEqual(response.status_code, 200)

        response = self.client.post(f"/objects/{self.object.pk}/attach-system/", {
            "system": str(self.system.pk),
            "status": "active",
            "implementation_date": "2026-01-01",
        })
        self.assertEqual(response.status_code, 302)
        link = ObjectSystem.objects.get(object=self.object, system=self.system)

        response = self.client.get(f"/objects/system-link/{link.pk}/edit/")
        self.assertEqual(response.status_code, 200)

        response = self.client.post(f"/objects/system-link/{link.pk}/edit/", {
            "object": str(self.object.pk),
            "system": str(self.second_system.pk),
            "status": "maintenance",
            "implementation_date": "2026-02-01",
            "next": "object",
        })
        self.assertEqual(response.status_code, 302)
        link.refresh_from_db()
        self.assertEqual(link.system_id, self.second_system.pk)
        self.assertEqual(link.status, "maintenance")

        response = self.client.post(f"/objects/system-link/{link.pk}/delete/", {"next": "object"})
        self.assertEqual(response.status_code, 302)
        self.assertFalse(ObjectSystem.objects.filter(pk=link.pk).exists())

    def test_authenticated_object_delete_endpoint_soft_deletes(self):
        self.client.force_login(self.user)
        response = self.client.post(f"/objects/{self.child.pk}/delete/")
        self.assertEqual(response.status_code, 302)
        self.child.refresh_from_db()
        self.assertTrue(self.child.is_deleted)


class ObjectsApiEndpointTests(ObjectsEndpointTestMixin, TestCase):
    def setUp(self):
        self.create_base_data()
        self.api_client = APIClient()

    def test_object_api_list_and_detail_are_public(self):
        response = self.api_client.get("/api/objects/objects/", {
            "category": str(self.category_l1.pk),
            "owner_entity": str(self.owner_entity.pk),
        })
        self.assertEqual(response.status_code, 200)

        response = self.api_client.get(f"/api/objects/objects/{self.object.pk}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], self.object.pk)
        self.assertEqual(response.data["owner_entity"], self.owner_entity.pk)

    def test_object_api_create_requires_authentication(self):
        response = self.api_client.post("/api/objects/objects/", {
            "name": "API объект",
            "level": 1,
            "category": self.category_l1.pk,
            "owner_entity": self.owner_entity.pk,
        }, format="json")
        self.assertIn(response.status_code, (401, 403))

    def test_authenticated_object_api_crud(self):
        self.api_client.force_authenticate(user=self.user)

        response = self.api_client.post("/api/objects/objects/", {
            "name": "API объект",
            "level": 1,
            "category": self.category_l1.pk,
            "owner_entity": self.owner_entity.pk,
        }, format="json")
        self.assertEqual(response.status_code, 201)
        object_id = response.data["id"]
        self.assertEqual(response.data["owner_entity"], self.owner_entity.pk)

        response = self.api_client.patch(f"/api/objects/objects/{object_id}/", {
            "name": "API объект изменен",
            "level": 1,
            "category": self.category_l1.pk,
            "owner_entity": self.owner_entity.pk,
        }, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["name"], "API объект изменен")

        response = self.api_client.delete(f"/api/objects/objects/{object_id}/")
        self.assertEqual(response.status_code, 204)
        deleted = Object.objects.get(pk=object_id)
        self.assertTrue(deleted.is_deleted)
