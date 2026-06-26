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


class ObjectSystemApiEndpointTests(ObjectsEndpointTestMixin, TestCase):
    def setUp(self):
        self.create_base_data()
        self.api_client = APIClient()
        self.link = ObjectSystem.objects.create(
            object=self.object,
            system=self.system,
            status="active",
        )

    def test_object_system_api_list_is_public(self):
        response = self.api_client.get("/api/objects/object-systems/")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(any(item["id"] == self.link.pk for item in response.data))

    def test_object_system_api_list_filtered_by_object(self):
        response = self.api_client.get(
            "/api/objects/object-systems/", {"object": str(self.object.pk)}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["system"], self.system.pk)

    def test_object_system_api_list_filtered_by_system(self):
        response = self.api_client.get(
            "/api/objects/object-systems/", {"system": str(self.system.pk)}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["object"], self.object.pk)

    def test_object_system_api_detail_is_public(self):
        response = self.api_client.get(f"/api/objects/object-systems/{self.link.pk}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], self.link.pk)
        self.assertEqual(response.data["status"], "active")

    def test_object_system_api_attach_requires_authentication(self):
        response = self.api_client.post(
            "/api/objects/object-systems/",
            {"object": self.object.pk, "system": self.second_system.pk},
            format="json",
        )
        self.assertIn(response.status_code, (401, 403))

    def test_authenticated_object_system_api_attach_update_detach(self):
        self.api_client.force_authenticate(user=self.user)

        # attach (create)
        response = self.api_client.post(
            "/api/objects/object-systems/",
            {
                "object": self.object.pk,
                "system": self.second_system.pk,
                "status": "planned",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        link_id = response.data["id"]
        self.assertEqual(response.data["system"], self.second_system.pk)

        # update (patch)
        response = self.api_client.patch(
            f"/api/objects/object-systems/{link_id}/",
            {"status": "maintenance"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "maintenance")

        # detach (delete)
        response = self.api_client.delete(f"/api/objects/object-systems/{link_id}/")
        self.assertEqual(response.status_code, 204)
        self.assertFalse(ObjectSystem.objects.filter(pk=link_id).exists())

    def test_object_system_api_attach_duplicate_is_rejected(self):
        self.api_client.force_authenticate(user=self.user)
        response = self.api_client.post(
            "/api/objects/object-systems/",
            {"object": self.object.pk, "system": self.system.pk},
            format="json",
        )
        # Уже привязана -> доменная ValidationError (422) или 400
        self.assertIn(response.status_code, (400, 422))


class ObjectOwnerHierarchyFilterTests(TestCase):
    """Иерархический фильтр по владельцу: выбор юр. лица должен включать в
    выборку и объекты его дочерних (на любую глубину) юр. лиц."""

    def setUp(self):
        self.user = User.objects.create_user(username="user", password="password")
        self.category = Category.objects.create(name="Площадка", level=1, creator_id=self.user)

        # Дерево владельцев: holding -> daughter -> grandchild
        self.holding = OwnerEntity.objects.create(owner_name="АО Холдинг")
        self.daughter = OwnerEntity.objects.create(
            owner_name="ООО Дочка",
            owner=self.holding,
            ultimate_owner=self.holding,
        )
        self.grandchild = OwnerEntity.objects.create(
            owner_name="ООО Внучка",
            owner=self.daughter,
            ultimate_owner=self.holding,
        )
        # Отдельная, не связанная с холдингом ветка
        self.other = OwnerEntity.objects.create(owner_name="ПАО Чужой")

        self.obj_holding = Object.objects.create(
            name="Объект холдинга", level=1, category=self.category,
            owner_entity=self.holding, creator_id=self.user,
        )
        self.obj_daughter = Object.objects.create(
            name="Объект дочки", level=1, category=self.category,
            owner_entity=self.daughter, creator_id=self.user,
        )
        self.obj_grandchild = Object.objects.create(
            name="Объект внучки", level=1, category=self.category,
            owner_entity=self.grandchild, creator_id=self.user,
        )
        self.obj_other = Object.objects.create(
            name="Чужой объект", level=1, category=self.category,
            owner_entity=self.other, creator_id=self.user,
        )

    def _names(self, qs):
        return set(qs.values_list("name", flat=True))

    def test_filter_by_root_includes_all_descendants(self):
        from apps.objects.usecases.object_usecase import ObjectUseCase
        result = ObjectUseCase().list(owner_entity=[self.holding.pk])
        self.assertEqual(
            self._names(result),
            {"Объект холдинга", "Объект дочки", "Объект внучки"},
        )
        self.assertNotIn("Чужой объект", self._names(result))

    def test_filter_by_middle_includes_its_descendants_only(self):
        from apps.objects.usecases.object_usecase import ObjectUseCase
        result = ObjectUseCase().list(owner_entity=[self.daughter.pk])
        # дочка + её потомок (внучка), но НЕ родитель (холдинг)
        self.assertEqual(
            self._names(result),
            {"Объект дочки", "Объект внучки"},
        )

    def test_filter_by_leaf_returns_only_itself(self):
        from apps.objects.usecases.object_usecase import ObjectUseCase
        result = ObjectUseCase().list(owner_entity=[self.grandchild.pk])
        self.assertEqual(self._names(result), {"Объект внучки"})

    def test_filter_is_resilient_to_cycles(self):
        # Искусственно создаём цикл: холдинг становится потомком внучки.
        self.holding.owner = self.grandchild
        self.holding.save()

        from apps.objects.usecases.object_usecase import ObjectUseCase
        # Не должно зациклиться; вернёт все объекты ветки.
        result = ObjectUseCase().list(owner_entity=[self.holding.pk])
        self.assertEqual(
            self._names(result),
            {"Объект холдинга", "Объект дочки", "Объект внучки"},
        )

    def test_web_object_list_filter_by_owner_includes_descendants(self):
        response = self.client.get("/objects/", {"owner_entity": str(self.holding.pk)})
        self.assertEqual(response.status_code, 200)
        objects = response.context["objects"]
        self.assertEqual(
            set(o.name for o in objects),
            {"Объект холдинга", "Объект дочки", "Объект внучки"},
        )

    def test_api_object_list_filter_by_owner_includes_descendants(self):
        api_client = APIClient()
        response = api_client.get(
            "/api/objects/objects/", {"owner_entity": str(self.holding.pk)}
        )
        self.assertEqual(response.status_code, 200)
        names = set(item["name"] for item in response.data)
        self.assertEqual(
            names, {"Объект холдинга", "Объект дочки", "Объект внучки"}
        )
