"""Серверная сортировка списков объектов и смежных сущностей через API."""
from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from apps.categories.models import Category
from apps.objects.models import Object
from apps.owners.models import OwnerEntity
from apps.entities.models import Entity


class ObjectApiOrderingTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("ord", "ord@x.x", "pw")
        Object.objects.create(name="Бета", level=1, creator_id=self.user)
        Object.objects.create(name="Альфа", level=1, creator_id=self.user)
        Object.objects.create(name="Гамма", level=1, creator_id=self.user)
        self.api = APIClient()

    def _names(self, ordering=None):
        params = {"ordering": ordering} if ordering else {}
        resp = self.api.get("/api/objects/objects/", params)
        self.assertEqual(resp.status_code, 200)
        return [r["name"] for r in resp.data]

    def test_default_ordering(self):
        self.assertEqual(self._names(), ["Альфа", "Бета", "Гамма"])

    def test_desc_ordering(self):
        self.assertEqual(self._names("-name"), ["Гамма", "Бета", "Альфа"])

    def test_invalid_ordering_falls_back(self):
        # произвольное поле игнорируется -> сортировка по умолчанию
        self.assertEqual(self._names("creator_id__password"), ["Альфа", "Бета", "Гамма"])


class OtherEntitiesApiOrderingTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("ord2", "o2@x.x", "pw")
        OwnerEntity.objects.create(owner_name="Бета")
        OwnerEntity.objects.create(owner_name="Альфа")
        Entity.objects.create(entity_name="Бета")
        Entity.objects.create(entity_name="Альфа")
        Category.objects.create(name="Бета", level=1, creator_id=self.user)
        Category.objects.create(name="Альфа", level=1, creator_id=self.user)
        self.api = APIClient()

    def test_owners_ordering_desc(self):
        resp = self.api.get("/api/owners/", {"ordering": "-owner_name"})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual([r["owner_name"] for r in resp.data], ["Бета", "Альфа"])

    def test_entities_ordering_desc(self):
        resp = self.api.get("/api/entities/", {"ordering": "-entity_name"})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual([r["entity_name"] for r in resp.data], ["Бета", "Альфа"])

    def test_categories_ordering_desc(self):
        resp = self.api.get("/api/categories/categories/", {"ordering": "-name"})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual([r["name"] for r in resp.data], ["Бета", "Альфа"])
