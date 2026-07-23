"""Тесты приложения объектов производства: HTML/API эндпоинты, наследование,
валидация уровней/титульного номера и сводка связанности."""
from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from apps.categories.models import Category
from apps.objects.models import Object, ObjectSystem
from apps.owners.models import OwnerEntity
from apps.system.models import AutomationSystem, AutomationClass


class ObjectsEndpointTestMixin:
    """Общие фикстуры для тестов объектов: пользователь, категории, системы, объекты."""
    def create_base_data(self):
        """Создаёт базовые фикстуры (пользователь, категории, системы, объекты)."""
        self.user = User.objects.create_user(username="user", password="password")
        self.category_l1 = Category.objects.create(category_name="Площадка", object_level=1, creator=self.user)
        self.category_l2 = Category.objects.create(category_name="Цех", object_level=2, creator=self.user)
        self.owner_entity = OwnerEntity.objects.create(owner_name="ООО Ромашка")
        self.automation_class = AutomationClass.objects.create(
            level=2,
            system_class="SCADA",
            description="Диспетчеризация",
        )
        self.system = AutomationSystem.objects.create(
            autosystem_name="АСУ ТП",
            system_class=self.automation_class,
            creator=self.user,
        )
        self.second_system = AutomationSystem.objects.create(
            autosystem_name="MES",
            system_class=self.automation_class,
            creator=self.user,
        )
        self.object = Object.objects.create(
            object_name="Завод",
            hierarchy_level=1,
            category=self.category_l1,
            owner_entity=self.owner_entity,
            creator=self.user,
        )
        self.child = Object.objects.create(
            object_name="Цех 1",
            hierarchy_level=2,
            parent_object=self.object,
            category=self.category_l2,
            owner_entity=self.owner_entity,
            creator=self.user,
        )


class ObjectsWebEndpointTests(ObjectsEndpointTestMixin, TestCase):
    """Тесты HTML-эндпоинтов объектов (список, детали, создание, фильтры)."""
    def setUp(self):
        """Готовит тестовые данные перед каждым тестом."""
        self.create_base_data()

    def test_object_list_page_is_available(self):
        """Страница списка объектов открывается (200)."""
        response = self.client.get("/objects/")
        self.assertEqual(response.status_code, 200)

    def test_object_list_supports_filters(self):
        """Список объектов поддерживает фильтры из GET-параметров."""
        response = self.client.get("/objects/", {
            "level": "1",
            "search": "завод",
            "category": str(self.category_l1.pk),
            "owner_entity": str(self.owner_entity.pk),
        })
        self.assertEqual(response.status_code, 200)

    def test_object_detail_page_is_available(self):
        """Страница деталей объекта открывается (200)."""
        response = self.client.get(f"/objects/{self.object.pk}/")
        self.assertEqual(response.status_code, 200)

    def test_object_create_page_requires_authentication(self):
        """Страница создания объекта требует авторизации."""
        response = self.client.get("/objects/create/")
        self.assertEqual(response.status_code, 302)

    def test_authenticated_object_create_and_edit_endpoints(self):
        """Авторизованный пользователь может создать и отредактировать объект."""
        self.client.force_login(self.user)

        response = self.client.get("/objects/create/")
        self.assertEqual(response.status_code, 200)

        response = self.client.post("/objects/create/", {
            "object_name": "Новый завод",
            "hierarchy_level": "1",
            "parent": "",
            "category": str(self.category_l1.pk),
            "owner_entity": str(self.owner_entity.pk),
        })
        self.assertEqual(response.status_code, 302)
        created = Object.objects.get(object_name="Новый завод")
        self.assertEqual(created.owner_entity_id, self.owner_entity.pk)

        response = self.client.get(f"/objects/{created.pk}/edit/")
        self.assertEqual(response.status_code, 200)

        response = self.client.post(f"/objects/{created.pk}/edit/", {
            "object_name": "Новый завод 2",
            "hierarchy_level": "1",
            "parent": "",
            "category": str(self.category_l1.pk),
            "owner_entity": str(self.owner_entity.pk),
        })
        self.assertEqual(response.status_code, 302)
        created.refresh_from_db()
        self.assertEqual(created.object_name, "Новый завод 2")

    def test_authenticated_object_add_child_endpoint(self):
        """Авторизованный пользователь может добавить дочерний объект."""
        self.client.force_login(self.user)

        response = self.client.get(f"/objects/{self.object.pk}/add-child/")
        self.assertEqual(response.status_code, 200)

        response = self.client.post(f"/objects/{self.object.pk}/add-child/", {
            "mode": "create",
            "object_name": "Цех 2",
            "hierarchy_level": "2",
            "category": str(self.category_l2.pk),
            "owner_entity": str(self.owner_entity.pk),
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Object.objects.filter(object_name="Цех 2", parent_object=self.object).exists())

    def test_authenticated_object_system_attach_edit_delete_endpoints(self):
        """Привязка, изменение и удаление системы у объекта (HTML)."""
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

    def test_authenticated_object_delete_endpoint_deletes(self):
        """Авторизованный пользователь удаляет объект."""
        self.client.force_login(self.user)
        child_pk = self.child.pk
        response = self.client.post(f"/objects/{child_pk}/delete/")
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Object.objects.filter(pk=child_pk).exists())


class ObjectsApiEndpointTests(ObjectsEndpointTestMixin, TestCase):
    """Тесты REST API объектов (список, детали, создание, обновление)."""
    def setUp(self):
        """Готовит тестовые данные перед каждым тестом."""
        self.create_base_data()
        self.api_client = APIClient()

    def test_object_api_list_and_detail_are_public(self):
        """Список и детали объектов доступны без авторизации (API)."""
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
        """Создание объекта через API требует авторизации."""
        response = self.api_client.post("/api/objects/objects/", {
            "object_name": "API объект",
            "hierarchy_level": 1,
            "category": self.category_l1.pk,
            "owner_entity": self.owner_entity.pk,
        }, format="json")
        self.assertIn(response.status_code, (401, 403))

    def test_authenticated_object_api_crud(self):
        """Полный CRUD объекта через API для авторизованного пользователя."""
        self.api_client.force_authenticate(user=self.user)

        response = self.api_client.post("/api/objects/objects/", {
            "object_name": "API объект",
            "hierarchy_level": 1,
            "category": self.category_l1.pk,
            "owner_entity": self.owner_entity.pk,
        }, format="json")
        self.assertEqual(response.status_code, 201)
        object_id = response.data["id"]
        self.assertEqual(response.data["owner_entity"], self.owner_entity.pk)

        response = self.api_client.patch(f"/api/objects/objects/{object_id}/", {
            "object_name": "API объект изменен",
            "hierarchy_level": 1,
            "category": self.category_l1.pk,
            "owner_entity": self.owner_entity.pk,
        }, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["object_name"], "API объект изменен")

        response = self.api_client.delete(f"/api/objects/objects/{object_id}/")
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Object.objects.filter(pk=object_id).exists())


class ObjectSystemApiEndpointTests(ObjectsEndpointTestMixin, TestCase):
    """Тесты REST API связей «система на объекте» (attach, update, detach)."""
    def setUp(self):
        """Готовит тестовые данные перед каждым тестом."""
        self.create_base_data()
        self.api_client = APIClient()
        self.link = ObjectSystem.objects.create(
            object=self.object,
            system=self.system,
            status="active",
        )

    def test_object_system_api_list_is_public(self):
        """Список связей доступен без авторизации (API)."""
        response = self.api_client.get("/api/objects/object-systems/")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(any(item["id"] == self.link.pk for item in response.data))

    def test_object_system_api_list_filtered_by_object(self):
        """Список связей фильтруется по объекту (API)."""
        response = self.api_client.get(
            "/api/objects/object-systems/", {"object": str(self.object.pk)}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["system"], self.system.pk)

    def test_object_system_api_list_filtered_by_system(self):
        """Список связей фильтруется по системе (API)."""
        response = self.api_client.get(
            "/api/objects/object-systems/", {"system": str(self.system.pk)}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["object"], self.object.pk)

    def test_object_system_api_detail_is_public(self):
        """Детали связи доступны без авторизации (API)."""
        response = self.api_client.get(f"/api/objects/object-systems/{self.link.pk}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], self.link.pk)
        self.assertEqual(response.data["status"], "active")

    def test_object_system_api_attach_requires_authentication(self):
        """Привязка системы через API требует авторизации."""
        response = self.api_client.post(
            "/api/objects/object-systems/",
            {"object": self.object.pk, "system": self.second_system.pk},
            format="json",
        )
        self.assertIn(response.status_code, (401, 403))

    def test_authenticated_object_system_api_attach_update_detach(self):
        """Привязка, обновление и отвязка системы через API."""
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
        """Повторная привязка той же системы к объекту отклоняется."""
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
        """Готовит тестовые данные перед каждым тестом."""
        self.user = User.objects.create_user(username="user", password="password")
        self.category = Category.objects.create(category_name="Площадка", object_level=1, creator=self.user)

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
            object_name="Объект холдинга", hierarchy_level=1, category=self.category,
            owner_entity=self.holding, creator=self.user,
        )
        self.obj_daughter = Object.objects.create(
            object_name="Объект дочки", hierarchy_level=1, category=self.category,
            owner_entity=self.daughter, creator=self.user,
        )
        self.obj_grandchild = Object.objects.create(
            object_name="Объект внучки", hierarchy_level=1, category=self.category,
            owner_entity=self.grandchild, creator=self.user,
        )
        self.obj_other = Object.objects.create(
            object_name="Чужой объект", hierarchy_level=1, category=self.category,
            owner_entity=self.other, creator=self.user,
        )

    def _names(self, qs):
        """Возвращает имена сущностей из ответа в порядке следования (вспомогательная)."""
        return set(qs.values_list("object_name", flat=True))

    def test_filter_by_root_includes_all_descendants(self):
        """Фильтр по корневому юр. лицу включает объекты всех потомков."""
        from apps.objects.usecases.object_usecase import ObjectUseCase
        result = ObjectUseCase().list(owner_entity=[self.holding.pk])
        self.assertEqual(
            self._names(result),
            {"Объект холдинга", "Объект дочки", "Объект внучки"},
        )
        self.assertNotIn("Чужой объект", self._names(result))

    def test_filter_by_middle_includes_its_descendants_only(self):
        """Фильтр по среднему юр. лицу включает только его потомков."""
        from apps.objects.usecases.object_usecase import ObjectUseCase
        result = ObjectUseCase().list(owner_entity=[self.daughter.pk])
        # дочка + её потомок (внучка), но НЕ родитель (холдинг)
        self.assertEqual(
            self._names(result),
            {"Объект дочки", "Объект внучки"},
        )

    def test_filter_by_leaf_returns_only_itself(self):
        """Фильтр по листовому юр. лицу возвращает только его объекты."""
        from apps.objects.usecases.object_usecase import ObjectUseCase
        result = ObjectUseCase().list(owner_entity=[self.grandchild.pk])
        self.assertEqual(self._names(result), {"Объект внучки"})

    def test_filter_is_resilient_to_cycles(self):
        # Искусственно создаём цикл: холдинг становится потомком внучки.
        """Иерархический фильтр устойчив к циклам в дереве владельцев."""
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
        """HTML-список: фильтр по владельцу включает объекты потомков."""
        response = self.client.get("/objects/", {"owner_entity": str(self.holding.pk)})
        self.assertEqual(response.status_code, 200)
        objects = response.context["objects"]
        self.assertEqual(
            set(o.object_name for o in objects),
            {"Объект холдинга", "Объект дочки", "Объект внучки"},
        )

    def test_api_object_list_filter_by_owner_includes_descendants(self):
        """API-список: фильтр по владельцу включает объекты потомков."""
        api_client = APIClient()
        response = api_client.get(
            "/api/objects/objects/", {"owner_entity": str(self.holding.pk)}
        )
        self.assertEqual(response.status_code, 200)
        names = set(item["object_name"] for item in response.data)
        self.assertEqual(
            names, {"Объект холдинга", "Объект дочки", "Объект внучки"}
        )


class ObjectNewFieldsTests(TestCase):
    """Новые поля объекта: описательные, характеристики, адрес, наследование
    адреса от родителя и ограничение title только 3-м уровнем."""

    def setUp(self):
        """Готовит тестовые данные перед каждым тестом."""
        self.user = User.objects.create_user(username="user", password="password")
        self.cat1 = Category.objects.create(category_name="Площадка", object_level=1, creator=self.user)
        self.cat2 = Category.objects.create(category_name="Цех", object_level=2, creator=self.user)
        self.cat3 = Category.objects.create(category_name="Установка", object_level=3, creator=self.user)
        self.api_client = APIClient()

    # ---------- usecase: создание с новыми полями ----------
    def test_usecase_create_persists_new_fields(self):
        """Use case create сохраняет все переданные поля объекта."""
        from apps.objects.usecases.object_usecase import ObjectUseCase
        obj = ObjectUseCase().create(
            user=self.user,
            object_name="Завод №1",
            hierarchy_level=1,
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
        """При отсутствии статуса объект создаётся в статусе active."""
        from apps.objects.usecases.object_usecase import ObjectUseCase
        obj = ObjectUseCase().create(user=self.user, object_name="Без статуса", hierarchy_level=1)
        self.assertEqual(obj.status, "active")

    # ---------- наследование адреса от родителя ----------
    def test_create_inherits_address_from_parent_when_not_provided(self):
        """Адрес наследуется от родителя, если не задан явно."""
        from apps.objects.usecases.object_usecase import ObjectUseCase
        uc = ObjectUseCase()
        parent = uc.create(
            user=self.user, object_name="Завод", hierarchy_level=1, category=self.cat1.pk,
            country="Россия", region="МО", city="Подольск", street="Ленина",
            house="1", title="",
        )
        child = uc.create(
            user=self.user, object_name="Цех 1", hierarchy_level=2, parent=parent.pk, category=self.cat2.pk,
        )
        child.refresh_from_db()
        self.assertEqual(child.country, "Россия")
        self.assertEqual(child.city, "Подольск")
        self.assertEqual(child.house, "1")
        self.assertEqual(child.street, "Ленина")

    # ---------- наследование юр. лица (owner_entity) от родителя ----------
    def test_child_inherits_owner_entity_from_parent(self):
        """Дочерний объект наследует юр. лицо от родителя."""
        from apps.objects.usecases.object_usecase import ObjectUseCase
        from apps.owners.models import OwnerEntity
        uc = ObjectUseCase()
        owner = OwnerEntity.objects.create(owner_name="ЮЛ-Родитель")
        parent = uc.create(
            user=self.user, object_name="Завод", hierarchy_level=1,
            category=self.cat1.pk, owner_entity=owner.pk,
        )
        child = uc.create(
            user=self.user, object_name="Цех", hierarchy_level=2,
            parent=parent.pk, category=self.cat2.pk,
        )
        child.refresh_from_db()
        self.assertEqual(child.owner_entity_id, owner.pk)

    def test_child_owner_entity_ignores_form_value_for_l2_l3(self):
        """Для L2/L3 значение из формы игнорируется — берётся от родителя."""
        from apps.objects.usecases.object_usecase import ObjectUseCase
        from apps.owners.models import OwnerEntity
        uc = ObjectUseCase()
        owner = OwnerEntity.objects.create(owner_name="ЮЛ-Родитель")
        other = OwnerEntity.objects.create(owner_name="ЮЛ-Чужой")
        parent = uc.create(
            user=self.user, object_name="Завод", hierarchy_level=1,
            category=self.cat1.pk, owner_entity=owner.pk,
        )
        child = uc.create(
            user=self.user, object_name="Цех", hierarchy_level=2, parent=parent.pk,
            category=self.cat2.pk, owner_entity=other.pk,  # попытка задать вручную
        )
        child.refresh_from_db()
        self.assertEqual(child.owner_entity_id, owner.pk)

    def test_child_owner_entity_empty_when_parent_has_none(self):
        """У ребёнка нет юр. лица, если у родителя оно не задано."""
        from apps.objects.usecases.object_usecase import ObjectUseCase
        uc = ObjectUseCase()
        parent = uc.create(
            user=self.user, object_name="Завод", hierarchy_level=1, category=self.cat1.pk,
        )
        child = uc.create(
            user=self.user, object_name="Цех", hierarchy_level=2,
            parent=parent.pk, category=self.cat2.pk,
        )
        child.refresh_from_db()
        self.assertIsNone(child.owner_entity_id)

    def test_update_reinherits_owner_entity_from_parent(self):
        """При смене родителя юр. лицо пере-наследуется."""
        from apps.objects.usecases.object_usecase import ObjectUseCase
        from apps.owners.models import OwnerEntity
        uc = ObjectUseCase()
        o1 = OwnerEntity.objects.create(owner_name="ЮЛ-1")
        o2 = OwnerEntity.objects.create(owner_name="ЮЛ-2")
        parent1 = uc.create(
            user=self.user, object_name="Завод1", hierarchy_level=1,
            category=self.cat1.pk, owner_entity=o1.pk,
        )
        parent2 = uc.create(
            user=self.user, object_name="Завод2", hierarchy_level=1,
            category=self.cat1.pk, owner_entity=o2.pk,
        )
        child = uc.create(
            user=self.user, object_name="Цех", hierarchy_level=2,
            parent=parent1.pk, category=self.cat2.pk,
        )
        # переносим ребёнка под другого родителя — владелец должен обновиться
        uc.update(pk=child.pk, user=self.user, parent=parent2.pk)
        child.refresh_from_db()
        self.assertEqual(child.owner_entity_id, o2.pk)

    def test_level1_keeps_form_owner_entity(self):
        """Для объекта 1-го уровня юр. лицо берётся из формы."""
        from apps.objects.usecases.object_usecase import ObjectUseCase
        from apps.owners.models import OwnerEntity
        uc = ObjectUseCase()
        owner = OwnerEntity.objects.create(owner_name="ЮЛ-1ур")
        obj = uc.create(
            user=self.user, object_name="Завод", hierarchy_level=1,
            category=self.cat1.pk, owner_entity=owner.pk,
        )
        obj.refresh_from_db()
        self.assertEqual(obj.owner_entity_id, owner.pk)

    def test_create_does_not_override_explicit_address(self):
        """Явно заданный адрес не перезаписывается адресом родителя."""
        from apps.objects.usecases.object_usecase import ObjectUseCase
        uc = ObjectUseCase()
        parent = uc.create(
            user=self.user, object_name="Завод", hierarchy_level=1, category=self.cat1.pk, city="Подольск",
        )
        child = uc.create(
            user=self.user, object_name="Цех 1", hierarchy_level=2, parent=parent.pk,
            category=self.cat2.pk, city="Климовск",
        )
        child.refresh_from_db()
        self.assertEqual(child.city, "Климовск")

    def test_get_parent_address_defaults_excludes_title(self):
        """Наследуемые адресные поля не включают титульный номер."""
        from apps.objects.usecases.object_usecase import ObjectUseCase
        uc = ObjectUseCase()
        parent = uc.create(
            user=self.user, object_name="Установка", hierarchy_level=3, parent=None,
            category=self.cat3.pk, city="Тула", title="Цех-А-стойка-3",
        )
        defaults = uc.get_parent_address_defaults(parent.pk)
        self.assertIn("city", defaults)
        self.assertNotIn("title", defaults)

    # ---------- ограничение title только уровнем 3 ----------
    def test_title_rejected_for_level_1_on_create(self):
        """Титульный номер на уровне 1 при создании отклоняется."""
        from apps.objects.usecases.object_usecase import ObjectUseCase
        from django.core.exceptions import ValidationError as DjangoValidationError
        with self.assertRaises(DjangoValidationError):
            ObjectUseCase().create(
                user=self.user, object_name="Завод", hierarchy_level=1, category=self.cat1.pk,
                title="недопустимо",
            )

    def test_title_allowed_for_level_2_and_3_on_create(self):
        """Титульный номер допустим на уровнях 2 и 3 при создании."""
        from apps.objects.usecases.object_usecase import ObjectUseCase
        uc = ObjectUseCase()
        l2 = uc.create(
            user=self.user, object_name="Цех", hierarchy_level=2, category=self.cat2.pk,
            title="Титул-2",
        )
        self.assertEqual(l2.title, "Титул-2")
        l3 = uc.create(
            user=self.user, object_name="Установка", hierarchy_level=3, category=self.cat3.pk,
            title="Цех-А-стойка-3",
        )
        self.assertEqual(l3.title, "Цех-А-стойка-3")

    def test_title_rejected_on_update_for_level_1(self):
        """Титульный номер на уровне 1 при обновлении отклоняется."""
        from apps.objects.usecases.object_usecase import ObjectUseCase
        from django.core.exceptions import ValidationError as DjangoValidationError
        uc = ObjectUseCase()
        obj = uc.create(user=self.user, object_name="Завод", hierarchy_level=1, category=self.cat1.pk)
        with self.assertRaises(DjangoValidationError):
            uc.update(pk=obj.pk, user=self.user, title="нельзя")

    # ---------- ограничение licensor только уровнем 3 ----------
    def test_licensor_allowed_only_for_level_3_on_create(self):
        """Лицензиар допустим на уровне 3 при создании."""
        from apps.objects.usecases.object_usecase import ObjectUseCase
        l3 = ObjectUseCase().create(
            user=self.user, object_name="Установка", hierarchy_level=3,
            category=self.cat3.pk, licensor="UOP",
        )
        self.assertEqual(l3.licensor, "UOP")

    def test_licensor_rejected_for_level_1_and_2_on_create(self):
        """Лицензиар на уровнях 1 и 2 при создании отклоняется."""
        from apps.objects.usecases.object_usecase import ObjectUseCase
        from django.core.exceptions import ValidationError as DjangoValidationError
        with self.assertRaises(DjangoValidationError):
            ObjectUseCase().create(
                user=self.user, object_name="Завод", hierarchy_level=1,
                category=self.cat1.pk, licensor="нельзя",
            )
        with self.assertRaises(DjangoValidationError):
            ObjectUseCase().create(
                user=self.user, object_name="Цех", hierarchy_level=2,
                category=self.cat2.pk, licensor="нельзя",
            )

    def test_licensor_rejected_on_update_for_non_level_3(self):
        """Лицензиар при обновлении объекта уровня 2 отклоняется."""
        from apps.objects.usecases.object_usecase import ObjectUseCase
        from django.core.exceptions import ValidationError as DjangoValidationError
        uc = ObjectUseCase()
        obj = uc.create(user=self.user, object_name="Цех", hierarchy_level=2, category=self.cat2.pk)
        with self.assertRaises(DjangoValidationError):
            uc.update(pk=obj.pk, user=self.user, licensor="нельзя")

    def test_web_create_level3_saves_licensor(self):
        """HTML-создание уровня 3 сохраняет лицензиара; на уровне 1 поле игнорируется."""
        from apps.objects.models import Object
        self.client.force_login(self.user)
        r = self.client.post("/objects/create/", {
            "object_name": "Установка ККФ",
            "hierarchy_level": "3",
            "category": str(self.cat3.pk),
            "status": "active",
            "licensor": "Lummus",
        })
        self.assertEqual(r.status_code, 302)
        obj = Object.objects.get(object_name="Установка ККФ")
        self.assertEqual(obj.licensor, "Lummus")
        # На уровне 1 поле licensor из формы не принимается.
        r2 = self.client.post("/objects/create/", {
            "object_name": "Завод НПЗ",
            "hierarchy_level": "1",
            "category": str(self.cat1.pk),
            "status": "active",
            "licensor": "должно игнорироваться",
        })
        self.assertEqual(r2.status_code, 302)
        obj1 = Object.objects.get(object_name="Завод НПЗ")
        self.assertEqual(obj1.licensor, "")

    def test_object_detail_shows_licensor_only_for_level_3(self):
        """Карточка объекта показывает «Лицензиар» только на уровне 3."""
        from apps.objects.usecases.object_usecase import ObjectUseCase
        uc = ObjectUseCase()
        l3 = uc.create(user=self.user, object_name="Установка Л", hierarchy_level=3,
                       category=self.cat3.pk, licensor="Технип")
        l1 = uc.create(user=self.user, object_name="Завод Л", hierarchy_level=1,
                       category=self.cat1.pk)
        self.client.force_login(self.user)
        h3 = self.client.get(f"/objects/{l3.pk}/").content.decode()
        self.assertIn("Лицензиар", h3)
        self.assertIn("Технип", h3)
        h1 = self.client.get(f"/objects/{l1.pk}/").content.decode()
        self.assertNotIn("Лицензиар", h1)

    # ---------- HTML формы: видимость полей по уровню ----------
    def test_form_hides_owner_group_for_non_level_1(self):
        """В форме редактирования L2/L3 группа «Юр. лицо» скрыта (display:none)."""
        import re
        from apps.objects.usecases.object_usecase import ObjectUseCase
        uc = ObjectUseCase()
        l1 = uc.create(user=self.user, object_name="Завод", hierarchy_level=1, category=self.cat1.pk)
        l2 = uc.create(user=self.user, object_name="Цех", hierarchy_level=2,
                       category=self.cat2.pk, parent=l1.pk)
        self.client.force_login(self.user)
        h2 = self.client.get(f"/objects/{l2.pk}/edit/").content.decode()
        m = re.search(r'id="ownerGroup"[^>]*style="([^"]*)"', h2)
        self.assertIsNotNone(m)
        self.assertIn("display:none", m.group(1))
        # На форме создания (по умолчанию L1) группа юр. лица видима.
        h1 = self.client.get("/objects/create/").content.decode()
        m1 = re.search(r'id="ownerGroup"[^>]*style="([^"]*)"', h1)
        self.assertTrue(m1 is None or "display:none" not in m1.group(1))

    def test_form_has_no_owner_inherit_hint_leftover(self):
        """Устаревший подсказочный блок ownerInheritHint удалён из формы."""
        self.client.force_login(self.user)
        h = self.client.get("/objects/create/").content.decode()
        self.assertNotIn('id="ownerInheritHint"', h)

    # ---------- HTML формы ----------
    def test_web_create_with_new_fields_and_title_level3(self):
        """HTML-создание уровня 3 сохраняет новые поля и титульный номер."""
        self.client.force_login(self.user)
        response = self.client.post("/objects/create/", {
            "object_name": "Установка X",
            "hierarchy_level": "3",
            "category": str(self.cat3.pk),
            "object_class": "установка",
            "status": "active",
            "city": "Самара",
            "title": "Цех-Б-3",
        })
        self.assertEqual(response.status_code, 302)
        obj = Object.objects.get(object_name="Установка X")
        self.assertEqual(obj.object_class, "установка")
        self.assertEqual(obj.city, "Самара")
        self.assertEqual(obj.title, "Цех-Б-3")

    def test_web_create_saves_title_for_level2(self):
        """HTML-создание уровня 2 сохраняет титульный номер."""
        self.client.force_login(self.user)
        # title теперь допустим и для уровня 2
        response = self.client.post("/objects/create/", {
            "object_name": "Цех Y",
            "hierarchy_level": "2",
            "category": str(self.cat2.pk),
            "title": "Титул-Цех-Y",
        })
        self.assertEqual(response.status_code, 302)
        obj = Object.objects.get(object_name="Цех Y")
        self.assertEqual(obj.title, "Титул-Цех-Y")

    def test_web_create_ignores_title_for_level1(self):
        """HTML-создание уровня 1 игнорирует титульный номер."""
        self.client.force_login(self.user)
        # title в POST есть, но уровень 1 -> view не должен его сохранять (и не падать)
        response = self.client.post("/objects/create/", {
            "object_name": "Завод Y",
            "hierarchy_level": "1",
            "category": str(self.cat1.pk),
            "title": "проигнорируется",
        })
        self.assertEqual(response.status_code, 302)
        obj = Object.objects.get(object_name="Завод Y")
        self.assertEqual(obj.title, "")

    # ---------- API ----------
    def test_api_create_with_new_fields(self):
        """API-создание сохраняет описательные и адресные поля."""
        self.api_client.force_authenticate(user=self.user)
        response = self.api_client.post("/api/objects/objects/", {
            "object_name": "API Установка",
            "hierarchy_level": 3,
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

    def test_api_create_title_allowed_for_level2(self):
        """API-создание уровня 2 принимает титульный номер."""
        self.api_client.force_authenticate(user=self.user)
        response = self.api_client.post("/api/objects/objects/", {
            "object_name": "API Цех",
            "hierarchy_level": 2,
            "category": self.cat2.pk,
            "title": "Титул-API-2",
        }, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["title"], "Титул-API-2")

    def test_api_create_title_rejected_for_level1(self):
        """API-создание уровня 1 отклоняет титульный номер."""
        self.api_client.force_authenticate(user=self.user)
        response = self.api_client.post("/api/objects/objects/", {
            "object_name": "API Завод",
            "hierarchy_level": 1,
            "category": self.cat1.pk,
            "title": "недопустимо",
        }, format="json")
        self.assertIn(response.status_code, (400, 422))

    def test_api_create_inherits_parent_address(self):
        """API-создание дочернего объекта наследует адрес родителя."""
        self.api_client.force_authenticate(user=self.user)
        parent_resp = self.api_client.post("/api/objects/objects/", {
            "object_name": "API Завод", "hierarchy_level": 1, "category": self.cat1.pk,
            "city": "Уфа", "country": "Россия",
        }, format="json")
        self.assertEqual(parent_resp.status_code, 201)
        parent_id = parent_resp.data["id"]

        child_resp = self.api_client.post("/api/objects/objects/", {
            "object_name": "API Цех", "hierarchy_level": 2, "parent": parent_id, "category": self.cat2.pk,
        }, format="json")
        self.assertEqual(child_resp.status_code, 201)
        self.assertEqual(child_resp.data["city"], "Уфа")
        self.assertEqual(child_resp.data["country"], "Россия")


class ObjectAddressLineTests(TestCase):
    """Тесты свойства address_line: сборка адреса строкой и добавление титульного номера."""
    def setUp(self):
        """Готовит тестовые данные перед каждым тестом."""
        self.user = User.objects.create_user(username="u2", password="pw")

    def test_address_line_joins_nonempty_parts(self):
        """address_line собирает адрес из непустых частей через запятую."""
        obj = Object.objects.create(
            object_name="O", hierarchy_level=1, country="Россия", region="", city="Москва",
            street="Ленина", house="1", creator=self.user,
        )
        self.assertEqual(obj.address_line, "Россия, Москва, Ленина, 1")

    def test_address_line_empty_when_no_address(self):
        """address_line пуст, если адресные поля не заданы."""
        obj = Object.objects.create(object_name="O", hierarchy_level=1, creator=self.user)
        self.assertEqual(obj.address_line, "")

    def test_address_line_appends_title_for_level_2_and_3(self):
        """address_line добавляет титульный номер на уровнях 2 и 3."""
        l3 = Object.objects.create(
            object_name="O3", hierarchy_level=3, city="Казань", title="Цех-А-3", creator=self.user,
        )
        self.assertEqual(l3.address_line, "Казань, Цех-А-3")
        # title теперь попадает в строку и для уровня 2
        l2 = Object.objects.create(
            object_name="O2", hierarchy_level=2, city="Казань", title="Титул-2", creator=self.user,
        )
        self.assertEqual(l2.address_line, "Казань, Титул-2")
        # на уровне 1 title в строку не попадает
        l1 = Object.objects.create(object_name="O1", hierarchy_level=1, city="Казань", creator=self.user)
        l1.title = "не должен показаться"
        self.assertEqual(l1.address_line, "Казань")


class ObjectSummaryExtendedTests(TestCase):
    """Расширенная сводка объекта: статусы внедрения и покрытие по уровням."""

    def setUp(self):
        """Готовит тестовые данные перед каждым тестом."""
        self.user = User.objects.create_user(username="sum", password="pw")
        self.client.force_login(self.user)
        self.cls_l1 = AutomationClass.objects.create(level=1, system_class="ПЛК")
        self.cls_l2 = AutomationClass.objects.create(level=2, system_class="SCADA")
        self.cls_l3 = AutomationClass.objects.create(level=3, system_class="MES")
        self.obj = Object.objects.create(
            object_name="Завод", hierarchy_level=1, creator=self.user
        )
        self.s1 = AutomationSystem.objects.create(
            autosystem_name="С1", system_class=self.cls_l2, creator=self.user)
        self.s2 = AutomationSystem.objects.create(
            autosystem_name="С2", system_class=self.cls_l2, creator=self.user)
        self.s3 = AutomationSystem.objects.create(
            autosystem_name="С3", system_class=self.cls_l3, creator=self.user)
        # 2 системы active (одна L2, одна L3), 1 planned (L2)
        ObjectSystem.objects.create(object=self.obj, system=self.s1, status="active")
        ObjectSystem.objects.create(object=self.obj, system=self.s3, status="active")
        ObjectSystem.objects.create(object=self.obj, system=self.s2, status="planned")

    def test_status_breakdown_counts(self):
        """Сводка: корректный подсчёт систем по статусам внедрения."""
        h = self.client.get(f"/objects/{self.obj.pk}/").content.decode()
        panel = h.split("summary-panel", 1)[1]
        self.assertIn("Статусы внедрения", panel)
        self.assertIn("В эксплуатации: 2", panel)
        self.assertIn("Планируется: 1", panel)
        # статусы без систем не показываются
        self.assertNotIn("Обслуживание", panel)

    def test_level_coverage_counts(self):
        """Сводка: корректный подсчёт покрытия по уровням автоматизации."""
        h = self.client.get(f"/objects/{self.obj.pk}/").content.decode()
        panel = h.split("summary-panel", 1)[1]
        self.assertIn("Покрытие по уровням", panel)
        # L2: 2 системы, L3: 1 система, остальные уровни — 0
        self.assertIn("L2: 2", panel)
        self.assertIn("L3: 1", panel)
        self.assertIn("L0: 0", panel)
        self.assertIn("L1: 0", panel)
        self.assertIn("L4: 0", panel)

    def test_zero_levels_dimmed(self):
        """Сводка: уровни без систем помечаются приглушённым классом."""
        h = self.client.get(f"/objects/{self.obj.pk}/").content.decode()
        panel = h.split("summary-panel", 1)[1]
        # уровень без систем помечен приглушённым классом
        self.assertIn("tag-off", panel)

    def test_children_categories_in_summary(self):
        """Сводка: показываются категории дочерних объектов."""
        cat = Category.objects.create(category_name="Цех переработки", object_level=2, creator=self.user)
        Object.objects.create(
            object_name="Цех-1", hierarchy_level=2, parent_object=self.obj,
            category=cat, creator=self.user)
        h = self.client.get(f"/objects/{self.obj.pk}/").content.decode()
        panel = h.split("summary-panel", 1)[1]
        self.assertIn("Категории дочерних", panel)
        self.assertIn("Цех переработки", panel)

    def test_system_status_is_colored_tag(self):
        """В таблице подключённых систем статус выводится цветным тегом."""
        h = self.client.get(f"/objects/{self.obj.pk}/").content.decode()
        # active -> tag-ok, planned -> tag-blue (согласно STATUS_TAG_CLASSES)
        self.assertIn('<span class="tag tag-ok">В эксплуатации</span>', h)
        self.assertIn('<span class="tag tag-blue">Планируется</span>', h)

    def test_objectsystem_status_tag_class_mapping(self):
        """Свойство status_tag_class связи возвращает верный css-класс."""
        os_active = ObjectSystem.objects.get(object=self.obj, system=self.s1)
        os_planned = ObjectSystem.objects.get(object=self.obj, system=self.s2)
        self.assertEqual(os_active.status_tag_class, "tag-ok")
        self.assertEqual(os_planned.status_tag_class, "tag-blue")

    def test_summary_groups_in_two_columns(self):
        """Группы сводки обёрнуты в двухколоночный контейнер."""
        h = self.client.get(f"/objects/{self.obj.pk}/").content.decode()
        self.assertIn("summary-cols", h)


class ObjectSystemImplementorRuleTests(TestCase):
    """Исполнитель внедрения: только интегратор / инж.компания / ФПЦ.

    Вендоры и поставщики не могут внедрять — ни в форме (фильтр списка),
    ни на бэкенде (валидация usecase).
    """

    def setUp(self):
        from apps.system.models import AutomationClass, AutomationSystem
        from apps.entities.usecases.entity_usecase import EntityUseCase
        self.user = User.objects.create_user("impl", "i@x.x", "pw")
        self.client.force_login(self.user)
        uc = EntityUseCase()
        self.vendor = uc.create(entity_name="ВендорИмпл", entity_type="vendor")
        self.supplier = uc.create(entity_name="ПоставщикИмпл", entity_type="supplier")
        self.integr = uc.create(entity_name="ИнтеграторИмпл", entity_type="system_integrator")
        self.eng = uc.create(entity_name="ИнжИмпл", entity_type="engineering_company")
        self.fcv = uc.create(entity_name="ФПЦИмпл", entity_type="full_cycle_vendor")
        cls = AutomationClass.objects.create(level=2, system_class="DCS")
        self.obj = Object.objects.create(object_name="ОбъИмпл", hierarchy_level=1, creator=self.user)
        self.system = AutomationSystem.objects.create(
            autosystem_name="СисИмпл", system_class=cls, creator=self.user)

    def _attach(self, implementor):
        from apps.objects.usecases.object_system_usecase import ObjectSystemUseCase
        return ObjectSystemUseCase().attach(
            object_pk=self.obj.pk, system=self.system.pk,
            status="planned", implementor=implementor.pk)

    def test_can_implement_flags(self):
        """Свойство can_implement: True у интегратора/инж/ФПЦ, False у вендора/поставщика."""
        self.assertTrue(self.integr.can_implement)
        self.assertTrue(self.eng.can_implement)
        self.assertTrue(self.fcv.can_implement)
        self.assertFalse(self.vendor.can_implement)
        self.assertFalse(self.supplier.can_implement)

    def test_vendor_rejected_as_implementor(self):
        """Вендор в качестве исполнителя — ValidationError."""
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            self._attach(self.vendor)

    def test_supplier_rejected_as_implementor(self):
        """Поставщик в качестве исполнителя — ValidationError."""
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            self._attach(self.supplier)

    def test_integrator_allowed_as_implementor(self):
        """Интегратор допустим как исполнитель."""
        link = self._attach(self.integr)
        self.assertEqual(link.implementor_id, self.integr.pk)

    def test_form_excludes_vendor_and_supplier(self):
        """Список исполнителей в форме не содержит вендоров/поставщиков.

        Проверяем именно блок пикера исполнителя (до пикера поставщика),
        так как вендор/поставщик легитимно присутствуют в списке поставщика.
        """
        h = self.client.get(f"/objects/{self.obj.pk}/attach-system/").content.decode()
        # Блок исполнителя — от его пикера до пикера поставщика.
        impl_block = h.split('id="selectedImplimentorId"')[0].split(
            "Исполнитель внедрения", 1)[-1]
        self.assertNotIn("ВендорИмпл", impl_block)
        self.assertNotIn("ПоставщикИмпл", impl_block)
        self.assertIn("ИнтеграторИмпл", impl_block)
        self.assertIn("ФПЦИмпл", impl_block)
        # В блоке поставщика должны быть только поставщик и ФПЦ.
        supplier_block = h.split('id="supplierPicker"', 1)[-1]
        self.assertIn("ПоставщикИмпл", supplier_block)
        self.assertIn("ФПЦИмпл", supplier_block)
        self.assertNotIn("ВендорИмпл", supplier_block)


class ObjectSystemSupplierRuleTests(TestCase):
    """ObjectSystem.supplier: только поставщик / вендор полного цикла.

    Плюс флаг «Поставляется вендором» — supplier становится вендором продукта.
    """

    def setUp(self):
        from apps.system.models import AutomationClass, VendorProduct, AutomationSystem
        from apps.entities.models import VendorProfile
        from apps.entities.usecases.entity_usecase import EntityUseCase
        from apps.objects.usecases.object_system_usecase import ObjectSystemUseCase
        self.user = User.objects.create_user("sup", "s@x.x", "pw")
        self.client.force_login(self.user)
        uc = EntityUseCase()
        self.vendor = uc.create(entity_name="ВендорС", entity_type="vendor")
        self.supplier = uc.create(entity_name="ПоставщикС", entity_type="supplier")
        self.integr = uc.create(entity_name="ИнтеграторС", entity_type="system_integrator")
        self.fcv = uc.create(entity_name="ФПЦС", entity_type="full_cycle_vendor")
        cls = AutomationClass.objects.create(level=2, system_class="DCS")
        # Продукт вендора + система на нём (для флага «поставляется вендором»).
        vp = VendorProfile.objects.get(entity=self.fcv)
        self.product = VendorProduct.objects.create(
            product_name="ПродС", vendor=vp, system_class=cls)
        self.system = AutomationSystem.objects.create(
            autosystem_name="СисС", system_class=cls, product=self.product, creator=self.user)
        self.obj = Object.objects.create(
            object_name="ОбъС", hierarchy_level=1, creator=self.user)
        self.os_uc = ObjectSystemUseCase()

    def test_supplier_ok(self):
        """Поставщик допустим как supplier."""
        link = self.os_uc.attach(object_pk=self.obj.pk, system=self.system.pk,
                                 status="planned", supplier=self.supplier.pk)
        self.assertEqual(link.supplier_id, self.supplier.pk)

    def test_fcv_ok(self):
        """Вендор полного цикла допустим как supplier."""
        link = self.os_uc.attach(object_pk=self.obj.pk, system=self.system.pk,
                                 status="planned", supplier=self.fcv.pk)
        self.assertEqual(link.supplier_id, self.fcv.pk)

    def test_vendor_rejected(self):
        """Обычный вендор не может быть поставщиком системы."""
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            self.os_uc.attach(object_pk=self.obj.pk, system=self.system.pk,
                              status="planned", supplier=self.vendor.pk)

    def test_integrator_rejected(self):
        """Интегратор не может быть поставщиком системы."""
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            self.os_uc.attach(object_pk=self.obj.pk, system=self.system.pk,
                              status="planned", supplier=self.integr.pk)

    def test_supplied_by_vendor_flag_sets_product_vendor(self):
        """Флаг «Поставляется вендором» ставит supplier = вендор продукта (ФПЦ)."""
        r = self.client.post(f"/objects/{self.obj.pk}/attach-system/", {
            "system": str(self.system.pk), "status": "planned",
            "supplied_by_vendor": "on"})
        self.assertEqual(r.status_code, 302)
        link = ObjectSystem.objects.get(object=self.obj, system=self.system)
        self.assertEqual(link.supplier_id, self.fcv.pk)

    def test_form_supplier_list_only_supplier_types(self):
        """Список поставщика в форме — только поставщик и ФПЦ (не вендор/интегратор)."""
        h = self.client.get(f"/objects/{self.obj.pk}/attach-system/").content.decode()
        block = h.split('id="supplierPicker"', 1)[-1]
        self.assertIn("ПоставщикС", block)
        self.assertIn("ФПЦС", block)
        self.assertNotIn("ВендорС", block)
        self.assertNotIn("ИнтеграторС", block)


class SupplierAddProductFormTests(TestCase):
    """Форма добавления поставляемого продукта: существующий / новый."""

    def setUp(self):
        from apps.system.models import AutomationClass, VendorProduct
        from apps.entities.models import VendorProfile
        from apps.entities.usecases.entity_usecase import EntityUseCase
        self.user = User.objects.create_user("sap", "sap@x.x", "pw")
        self.client.force_login(self.user)
        uc = EntityUseCase()
        self.supplier = uc.create(entity_name="ПоставщикФ", entity_type="supplier")
        self.vendor = uc.create(entity_name="ВендорФ", entity_type="vendor")
        cls = AutomationClass.objects.create(level=2, system_class="DCS")
        vp = VendorProfile.objects.get(entity=self.vendor)
        self.product = VendorProduct.objects.create(
            product_name="СуществующийПродукт", vendor=vp, system_class=cls)

    def test_form_opens_with_toggle(self):
        """Форма открывается и содержит переключатель режимов."""
        h = self.client.get(
            f"/entities/{self.supplier.pk}/add-supplied-product/").content.decode()
        self.assertIn("mode-toggle", h)
        self.assertIn("СуществующийПродукт", h)

    def test_attach_existing(self):
        """Режим «существующий» привязывает продукт к поставщику."""
        r = self.client.post(
            f"/entities/{self.supplier.pk}/add-supplied-product/",
            {"mode": "existing", "existing_product": str(self.product.pk)})
        self.assertEqual(r.status_code, 302)
        self.assertTrue(
            self.supplier.supplier_profile.products.filter(pk=self.product.pk).exists())

    def test_create_new(self):
        """Режим «новый» создаёт продукт и привязывает к поставщику."""
        r = self.client.post(
            f"/entities/{self.supplier.pk}/add-supplied-product/",
            {"mode": "create", "product_name": "НовыйФ", "vendor": ""})
        self.assertEqual(r.status_code, 302)
        from apps.system.models import VendorProduct
        p = VendorProduct.objects.get(product_name="НовыйФ")
        self.assertTrue(
            self.supplier.supplier_profile.products.filter(pk=p.pk).exists())

    def test_non_supplier_redirected(self):
        """Не-поставщик не может открыть форму (редирект на карточку)."""
        r = self.client.get(
            f"/entities/{self.vendor.pk}/add-supplied-product/")
        self.assertEqual(r.status_code, 302)


class ObjectSystemSupplierFilterTests(TestCase):
    """Список поставщиков в форме ограничен поставщиками продукта системы."""

    def setUp(self):
        from apps.system.models import AutomationClass, VendorProduct, AutomationSystem
        from apps.entities.usecases.entity_usecase import EntityUseCase
        self.user = User.objects.create_user("supf", "supf@x.x", "pw")
        self.client.force_login(self.user)
        uc = EntityUseCase()
        # Два поставщика: один поставляет продукт системы, другой — нет.
        self.sup_yes = uc.create(entity_name="ПоставщикДА", entity_type="supplier")
        self.sup_no = uc.create(entity_name="ПоставщикНЕТ", entity_type="supplier")
        cls = AutomationClass.objects.create(level=2, system_class="DCS")
        self.product = VendorProduct.objects.create(product_name="ПродФильтр", system_class=cls)
        uc.save_supplier_products(self.sup_yes, product_ids=[self.product.pk])
        self.system = AutomationSystem.objects.create(
            autosystem_name="СисФильтр", system_class=cls, product=self.product, creator=self.user)
        self.obj = Object.objects.create(
            object_name="ОбъФильтр", hierarchy_level=1, creator=self.user)

    def test_system_side_lists_only_product_suppliers(self):
        """Форма со стороны системы: в списке только поставщики продукта."""
        h = self.client.get(f"/system/{self.system.pk}/attach-object/").content.decode()
        block = h.split('id="supplierPicker"', 1)[-1].split('name="supplier"', 1)[0]
        self.assertIn("ПоставщикДА", block)
        self.assertNotIn("ПоставщикНЕТ", block)

    def test_object_side_system_carries_supplier_ids(self):
        """Форма со стороны объекта: у системы data-suppliers с id поставщиков продукта."""
        h = self.client.get(f"/objects/{self.obj.pk}/attach-system/").content.decode()
        import re
        m = re.search(
            r'data-id="%d"[^>]*data-suppliers="([^"]*)"' % self.system.pk, h)
        self.assertIsNotNone(m)
        ids = m.group(1).split(",") if m.group(1) else []
        self.assertIn(str(self.sup_yes.pk), ids)
        self.assertNotIn(str(self.sup_no.pk), ids)


class ObjectAddressByLevelTests(TestCase):
    """Адрес: у L1 — полный, у L2/L3 — кодовое расположение (title)."""

    def setUp(self):
        self.user = User.objects.create_user("addr", "a@x.x", "pw")
        self.l1 = Object.objects.create(
            object_name="Завод", hierarchy_level=1, creator=self.user,
            country="Россия", region="Тульская область", city="Тула")
        self.l3 = Object.objects.create(
            object_name="Установка", hierarchy_level=3, parent_object=self.l1,
            creator=self.user, title="У-42", city="Тула")

    def test_l1_shows_full_address(self):
        h = self.client.get(f"/objects/{self.l1.pk}/").content.decode()
        legal = h.split("Юридическая информация", 1)[1].split("Характеристики", 1)[0]
        self.assertIn("Адрес", legal)
        self.assertIn("Тульская область", legal)

    def test_l3_shows_title_not_full_address(self):
        h = self.client.get(f"/objects/{self.l3.pk}/").content.decode()
        legal = h.split("Юридическая информация", 1)[1].split("Характеристики", 1)[0]
        self.assertIn("У-42", legal)
        self.assertNotIn("Тульская область", legal)

    def test_reconstruction_in_characteristics(self):
        h = self.client.get(f"/objects/{self.l1.pk}/").content.decode()
        char = h.split("Характеристики", 1)[1].split("Сводка", 1)[0]
        self.assertIn("Реконструкция", char)
