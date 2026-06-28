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


class ObjectNewFieldsTests(TestCase):
    """Новые поля объекта: описательные, характеристики, адрес, наследование
    адреса от родителя и ограничение title только 3-м уровнем."""

    def setUp(self):
        self.user = User.objects.create_user(username="user", password="password")
        self.cat1 = Category.objects.create(name="Площадка", level=1, creator_id=self.user)
        self.cat2 = Category.objects.create(name="Цех", level=2, creator_id=self.user)
        self.cat3 = Category.objects.create(name="Установка", level=3, creator_id=self.user)
        self.api_client = APIClient()

    # ---------- usecase: создание с новыми полями ----------
    def test_usecase_create_persists_new_fields(self):
        from apps.objects.usecases.object_usecase import ObjectUseCase
        obj = ObjectUseCase().create(
            user=self.user,
            name="Завод №1",
            level=1,
            category=self.cat1.pk,
            object_short_name="З1",
            object_class="завод",
            status="in_project",
            capacity="100 т/год",
            is_reconstructed=True,
            country="Россия",
            city="Москва",
        )
        obj.refresh_from_db()
        self.assertEqual(obj.object_short_name, "З1")
        self.assertEqual(obj.object_class, "завод")
        self.assertEqual(obj.status, "in_project")
        self.assertEqual(obj.capacity, "100 т/год")
        self.assertTrue(obj.is_reconstructed)
        self.assertEqual(obj.country, "Россия")
        self.assertEqual(obj.city, "Москва")

    def test_status_defaults_to_active(self):
        from apps.objects.usecases.object_usecase import ObjectUseCase
        obj = ObjectUseCase().create(user=self.user, name="Без статуса", level=1)
        self.assertEqual(obj.status, "active")

    # ---------- наследование адреса от родителя ----------
    def test_create_inherits_address_from_parent_when_not_provided(self):
        from apps.objects.usecases.object_usecase import ObjectUseCase
        uc = ObjectUseCase()
        parent = uc.create(
            user=self.user, name="Завод", level=1, category=self.cat1.pk,
            country="Россия", region="МО", city="Подольск", street="Ленина",
            house="1", fias_code="ABC", title="",
        )
        child = uc.create(
            user=self.user, name="Цех 1", level=2, parent=parent.pk, category=self.cat2.pk,
        )
        child.refresh_from_db()
        self.assertEqual(child.country, "Россия")
        self.assertEqual(child.city, "Подольск")
        self.assertEqual(child.house, "1")
        self.assertEqual(child.fias_code, "ABC")

    def test_create_does_not_override_explicit_address(self):
        from apps.objects.usecases.object_usecase import ObjectUseCase
        uc = ObjectUseCase()
        parent = uc.create(
            user=self.user, name="Завод", level=1, category=self.cat1.pk, city="Подольск",
        )
        child = uc.create(
            user=self.user, name="Цех 1", level=2, parent=parent.pk,
            category=self.cat2.pk, city="Климовск",
        )
        child.refresh_from_db()
        self.assertEqual(child.city, "Климовск")

    def test_get_parent_address_defaults_excludes_title(self):
        from apps.objects.usecases.object_usecase import ObjectUseCase
        uc = ObjectUseCase()
        parent = uc.create(
            user=self.user, name="Установка", level=3, parent=None,
            category=self.cat3.pk, city="Тула", title="Цех-А-стойка-3",
        )
        defaults = uc.get_parent_address_defaults(parent.pk)
        self.assertIn("city", defaults)
        self.assertNotIn("title", defaults)

    # ---------- ограничение title только уровнем 3 ----------
    def test_title_rejected_for_non_level_3_on_create(self):
        from apps.objects.usecases.object_usecase import ObjectUseCase
        from django.core.exceptions import ValidationError as DjangoValidationError
        with self.assertRaises(DjangoValidationError):
            ObjectUseCase().create(
                user=self.user, name="Цех", level=2, category=self.cat2.pk,
                title="недопустимо",
            )

    def test_title_allowed_for_level_3_on_create(self):
        from apps.objects.usecases.object_usecase import ObjectUseCase
        obj = ObjectUseCase().create(
            user=self.user, name="Установка", level=3, category=self.cat3.pk,
            title="Цех-А-стойка-3",
        )
        self.assertEqual(obj.title, "Цех-А-стойка-3")

    def test_title_rejected_on_update_for_non_level_3(self):
        from apps.objects.usecases.object_usecase import ObjectUseCase
        from django.core.exceptions import ValidationError as DjangoValidationError
        uc = ObjectUseCase()
        obj = uc.create(user=self.user, name="Цех", level=2, category=self.cat2.pk)
        with self.assertRaises(DjangoValidationError):
            uc.update(pk=obj.pk, user=self.user, title="нельзя")

    # ---------- HTML формы ----------
    def test_web_create_with_new_fields_and_title_level3(self):
        self.client.force_login(self.user)
        response = self.client.post("/objects/create/", {
            "name": "Установка X",
            "level": "3",
            "category": str(self.cat3.pk),
            "object_class": "установка",
            "status": "active",
            "city": "Самара",
            "title": "Цех-Б-3",
        })
        self.assertEqual(response.status_code, 302)
        obj = Object.objects.get(name="Установка X")
        self.assertEqual(obj.object_class, "установка")
        self.assertEqual(obj.city, "Самара")
        self.assertEqual(obj.title, "Цех-Б-3")

    def test_web_create_ignores_title_for_non_level3(self):
        self.client.force_login(self.user)
        # title в POST есть, но уровень не 3 -> view не должен его сохранять (и не падать)
        response = self.client.post("/objects/create/", {
            "name": "Цех Y",
            "level": "2",
            "category": str(self.cat2.pk),
            "title": "проигнорируется",
        })
        self.assertEqual(response.status_code, 302)
        obj = Object.objects.get(name="Цех Y")
        self.assertEqual(obj.title, "")

    # ---------- API ----------
    def test_api_create_with_new_fields(self):
        self.api_client.force_authenticate(user=self.user)
        response = self.api_client.post("/api/objects/objects/", {
            "name": "API Установка",
            "level": 3,
            "category": self.cat3.pk,
            "object_class": "установка",
            "status": "stopped",
            "city": "Казань",
            "title": "Цех-В-7",
        }, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["object_class"], "установка")
        self.assertEqual(response.data["status"], "stopped")
        self.assertEqual(response.data["city"], "Казань")
        self.assertEqual(response.data["title"], "Цех-В-7")

    def test_api_create_title_rejected_for_non_level3(self):
        self.api_client.force_authenticate(user=self.user)
        response = self.api_client.post("/api/objects/objects/", {
            "name": "API Цех",
            "level": 2,
            "category": self.cat2.pk,
            "title": "недопустимо",
        }, format="json")
        self.assertIn(response.status_code, (400, 422))

    def test_api_create_inherits_parent_address(self):
        self.api_client.force_authenticate(user=self.user)
        parent_resp = self.api_client.post("/api/objects/objects/", {
            "name": "API Завод", "level": 1, "category": self.cat1.pk,
            "city": "Уфа", "country": "Россия",
        }, format="json")
        self.assertEqual(parent_resp.status_code, 201)
        parent_id = parent_resp.data["id"]

        child_resp = self.api_client.post("/api/objects/objects/", {
            "name": "API Цех", "level": 2, "parent": parent_id, "category": self.cat2.pk,
        }, format="json")
        self.assertEqual(child_resp.status_code, 201)
        self.assertEqual(child_resp.data["city"], "Уфа")
        self.assertEqual(child_resp.data["country"], "Россия")


class ObjectAddressLineTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="u2", password="pw")

    def test_address_line_joins_nonempty_parts(self):
        obj = Object.objects.create(
            name="O", level=1, country="Россия", region="", city="Москва",
            street="Ленина", house="1", creator_id=self.user,
        )
        self.assertEqual(obj.address_line, "Россия, Москва, Ленина, 1")

    def test_address_line_empty_when_no_address(self):
        obj = Object.objects.create(name="O", level=1, creator_id=self.user)
        self.assertEqual(obj.address_line, "")

    def test_address_line_appends_title_only_for_level_3(self):
        l3 = Object.objects.create(
            name="O3", level=3, city="Казань", title="Цех-А-3", creator_id=self.user,
        )
        self.assertEqual(l3.address_line, "Казань, Цех-А-3")
        # на уровне != 3 title в строку не попадает (даже если каким-то образом задан)
        l2 = Object.objects.create(name="O2", level=2, city="Казань", creator_id=self.user)
        l2.title = "не должен показаться"
        self.assertEqual(l2.address_line, "Казань")
