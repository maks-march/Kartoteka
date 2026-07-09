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
        self.category = Category.objects.create(category_name="Площадка", object_level=1, creator_id=self.user)
        self.object = Object.objects.create(
            object_name="Завод",
            hierarchy_level=1,
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
            object_name="Непривязанный объект",
            hierarchy_level=1,
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

    def test_owner_entity_api_attach_object_requires_authentication(self):
        unassigned_object = Object.objects.create(
            object_name="Непривязанный объект",
            hierarchy_level=1,
            category=self.category,
            creator_id=self.user,
        )
        response = self.api_client.post(
            f"/api/owners/{self.owner.pk}/attach-object/",
            {"object": unassigned_object.pk},
            format="json",
        )
        self.assertIn(response.status_code, (401, 403))

    def test_authenticated_owner_entity_api_attach_object(self):
        self.api_client.force_authenticate(user=self.user)
        unassigned_object = Object.objects.create(
            object_name="Непривязанный объект",
            hierarchy_level=1,
            category=self.category,
            creator_id=self.user,
        )

        response = self.api_client.post(
            f"/api/owners/{self.owner.pk}/attach-object/",
            {"object": unassigned_object.pk},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["owner_entity"], self.owner.pk)
        unassigned_object.refresh_from_db()
        self.assertEqual(unassigned_object.owner_entity_id, self.owner.pk)

    def test_owner_entity_api_attach_object_unknown_owner_returns_404(self):
        self.api_client.force_authenticate(user=self.user)
        response = self.api_client.post(
            "/api/owners/999999/attach-object/",
            {"object": self.object.pk},
            format="json",
        )
        self.assertEqual(response.status_code, 404)


class OwnerEntityDescendantsTests(TestCase):
    def setUp(self):
        self.repo = __import__(
            "apps.owners.repositories.owner_entity_repository",
            fromlist=["OwnerEntityRepository"],
        ).OwnerEntityRepository()
        self.root = OwnerEntity.objects.create(owner_name="Корень")
        self.child_a = OwnerEntity.objects.create(owner_name="Дочка A", owner=self.root)
        self.child_b = OwnerEntity.objects.create(owner_name="Дочка B", owner=self.root)
        self.grandchild = OwnerEntity.objects.create(owner_name="Внучка", owner=self.child_a)
        self.unrelated = OwnerEntity.objects.create(owner_name="Несвязанный")

    def test_descendants_of_root_include_whole_tree(self):
        ids = self.repo.get_descendant_ids([self.root.pk])
        self.assertEqual(
            ids,
            {self.root.pk, self.child_a.pk, self.child_b.pk, self.grandchild.pk},
        )

    def test_descendants_of_leaf_is_itself(self):
        ids = self.repo.get_descendant_ids([self.grandchild.pk])
        self.assertEqual(ids, {self.grandchild.pk})

    def test_descendants_handles_multiple_roots_and_ignores_empty(self):
        ids = self.repo.get_descendant_ids([self.child_a.pk, self.unrelated.pk, "", None])
        self.assertEqual(ids, {self.child_a.pk, self.grandchild.pk, self.unrelated.pk})

    def test_descendants_resilient_to_cycle(self):
        # цикл: корень -> дочка A -> внучка -> корень
        self.root.owner = self.grandchild
        self.root.save()
        ids = self.repo.get_descendant_ids([self.root.pk])
        self.assertEqual(
            ids,
            {self.root.pk, self.child_a.pk, self.child_b.pk, self.grandchild.pk},
        )


class OwnerIsRootTests(TestCase):
    """Флаг is_root (материнская компания) и фильтр по материнским."""

    def setUp(self):
        self.user = User.objects.create_user("root", "r@r.r", "pw")
        self.mother = OwnerEntity.objects.create(owner_name="Материнская АО")
        self.sub = OwnerEntity.objects.create(owner_name="Дочерняя ООО", owner=self.mother)

    def test_is_root_auto_true_when_no_owner(self):
        self.assertTrue(self.mother.is_root)

    def test_is_root_auto_false_when_has_owner(self):
        self.assertFalse(self.sub.is_root)

    def test_is_root_recomputed_on_owner_change(self):
        self.mother.owner = OwnerEntity.objects.create(owner_name="Новая мать")
        self.mother.save()
        self.mother.refresh_from_db()
        self.assertFalse(self.mother.is_root)
        self.sub.owner = None
        self.sub.save()
        self.sub.refresh_from_db()
        self.assertTrue(self.sub.is_root)

    def test_is_root_manual_value_ignored(self):
        m = OwnerEntity(owner_name="Форс", owner=None, is_root=False)
        m.save()
        self.assertTrue(m.is_root)

    def test_list_roots_returns_only_mothers(self):
        from apps.owners.usecases.owner_entity_usecase import OwnerEntityUseCase
        roots = list(OwnerEntityUseCase().list_roots())
        self.assertIn(self.mother, roots)
        self.assertNotIn(self.sub, roots)


class ObjectFilterByMotherTests(TestCase):
    """Фильтр объектов по материнской подтягивает объекты дочерних управляющих."""

    def setUp(self):
        self.user = User.objects.create_user("of", "of@x.x", "pw")
        self.mother = OwnerEntity.objects.create(owner_name="Мать-Холдинг")
        self.sub = OwnerEntity.objects.create(owner_name="Дочка-Упр", owner=self.mother)
        self.obj_sub = Object.objects.create(
            object_name="Объект дочки", hierarchy_level=1, owner_entity=self.sub, creator_id=self.user)
        self.obj_mother = Object.objects.create(
            object_name="Объект матери", hierarchy_level=1, owner_entity=self.mother, creator_id=self.user)
        self.obj_other = Object.objects.create(
            object_name="Чужой объект", hierarchy_level=1, creator_id=self.user)

    def test_filter_by_mother_includes_subsidiary_objects(self):
        from apps.objects.usecases.object_usecase import ObjectUseCase
        names = sorted(o.object_name for o in ObjectUseCase().list(owner_entity=[self.mother.pk]))
        self.assertEqual(names, ["Объект дочки", "Объект матери"])

    def test_object_list_owner_filter_offers_only_mothers(self):
        h = self.client.get("/objects/").content.decode()
        self.assertIn("Материнская компания", h)
        picker = h.split('id="ownerEntityFilterList"', 1)[1].split("</div>\n                    <div", 1)[0]
        self.assertIn("Мать-Холдинг", picker)
        self.assertNotIn("Дочка-Упр", picker)
