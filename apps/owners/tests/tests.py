from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from apps.categories.models import Category
from apps.objects.models import Object
from apps.owners.models import OwnerEntity


class OwnersEndpointTestMixin:
    def create_base_data(self):
        self.user = User.objects.create_user(username="user", password="password")
        self.root_owner = OwnerEntity.objects.create(owner_name="АО Холдинг")
        self.owner = OwnerEntity.objects.create(
            owner_name="ООО Завод",
            owner=self.root_owner,
            ultimate_owner=self.root_owner,
        )
        self.category = Category.objects.create(name="Площадка", level=1, creator_id=self.user)
        self.object = Object.objects.create(
            name="Завод",
            level=1,
            category=self.category,
            owner_entity=self.owner,
            creator_id=self.user,
        )


class OwnersWebEndpointTests(OwnersEndpointTestMixin, TestCase):
    def setUp(self):
        self.create_base_data()

    def test_owner_entity_list_page_is_available(self):
        response = self.client.get("/owners/")
        self.assertEqual(response.status_code, 200)

    def test_owner_entity_list_supports_search(self):
        response = self.client.get("/owners/", {"search": "завод"})
        self.assertEqual(response.status_code, 200)

    def test_owner_entity_detail_page_is_available(self):
        response = self.client.get(f"/owners/{self.owner.pk}/")
        self.assertEqual(response.status_code, 200)

    def test_owner_entity_create_page_requires_authentication(self):
        response = self.client.get("/owners/create/")
        self.assertEqual(response.status_code, 302)

    def test_owner_entity_attach_object_page_requires_authentication(self):
        response = self.client.get(f"/owners/{self.owner.pk}/attach-object/")
        self.assertEqual(response.status_code, 302)

    def test_authenticated_owner_entity_attach_object_endpoint(self):
        self.client.force_login(self.user)
        unassigned_object = Object.objects.create(
            name="Непривязанный объект",
            level=1,
            category=self.category,
            creator_id=self.user,
        )

        response = self.client.get(f"/owners/{self.owner.pk}/attach-object/")
        self.assertEqual(response.status_code, 200)

        response = self.client.post(f"/owners/{self.owner.pk}/attach-object/", {
            "object": str(unassigned_object.pk),
        })
        self.assertEqual(response.status_code, 302)
        unassigned_object.refresh_from_db()
        self.assertEqual(unassigned_object.owner_entity_id, self.owner.pk)

    def test_authenticated_owner_entity_crud_endpoints(self):
        self.client.force_login(self.user)

        response = self.client.get("/owners/create/")
        self.assertEqual(response.status_code, 200)

        response = self.client.post("/owners/create/", {
            "owner_name": "ООО Дочка",
            "owner": str(self.root_owner.pk),
            "ultimate_owner": str(self.root_owner.pk),
        })
        self.assertEqual(response.status_code, 302)
        created = OwnerEntity.objects.get(owner_name="ООО Дочка")
        self.assertEqual(created.owner_id, self.root_owner.pk)
        self.assertEqual(created.ultimate_owner_id, self.root_owner.pk)

        response = self.client.get(f"/owners/{created.pk}/edit/")
        self.assertEqual(response.status_code, 200)

        response = self.client.post(f"/owners/{created.pk}/edit/", {
            "owner_name": "ООО Дочка 2",
            "owner": str(self.root_owner.pk),
            "ultimate_owner": str(self.root_owner.pk),
        })
        self.assertEqual(response.status_code, 302)
        created.refresh_from_db()
        self.assertEqual(created.owner_name, "ООО Дочка 2")

        response = self.client.post(f"/owners/{created.pk}/delete/")
        self.assertEqual(response.status_code, 302)
        self.assertFalse(OwnerEntity.objects.filter(pk=created.pk).exists())


class OwnersApiEndpointTests(OwnersEndpointTestMixin, TestCase):
    def setUp(self):
        self.create_base_data()
        self.api_client = APIClient()

    def test_owner_entity_api_list_and_detail_are_public(self):
        response = self.api_client.get("/api/owners/", {"search": "завод"})
        self.assertEqual(response.status_code, 200)

        response = self.api_client.get(f"/api/owners/{self.owner.pk}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], self.owner.pk)
        self.assertEqual(response.data["owner"], self.root_owner.pk)
        self.assertEqual(response.data["ultimate_owner"], self.root_owner.pk)

    def test_owner_entity_api_create_requires_authentication(self):
        response = self.api_client.post("/api/owners/", {
            "owner_name": "ООО API",
            "owner": self.root_owner.pk,
            "ultimate_owner": self.root_owner.pk,
        }, format="json")
        self.assertIn(response.status_code, (401, 403))

    def test_authenticated_owner_entity_api_crud(self):
        self.api_client.force_authenticate(user=self.user)

        response = self.api_client.post("/api/owners/", {
            "owner_name": "ООО API",
            "owner": self.root_owner.pk,
            "ultimate_owner": self.root_owner.pk,
        }, format="json")
        self.assertEqual(response.status_code, 201)
        owner_id = response.data["id"]
        self.assertEqual(response.data["owner"], self.root_owner.pk)
        self.assertEqual(response.data["ultimate_owner"], self.root_owner.pk)

        response = self.api_client.patch(f"/api/owners/{owner_id}/", {
            "owner_name": "ООО API 2",
            "owner": self.root_owner.pk,
            "ultimate_owner": self.root_owner.pk,
        }, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["owner_name"], "ООО API 2")

        response = self.api_client.delete(f"/api/owners/{owner_id}/")
        self.assertEqual(response.status_code, 204)
        self.assertFalse(OwnerEntity.objects.filter(pk=owner_id).exists())
