"""UI серверной сортировки: результат сортировки и поведение ссылок-заголовков.

Цикл по клику: нет → по убыванию → по возрастанию → выключить.
Сортировка многоуровневая (последний столбец — последний ключ).
"""
from django.contrib.auth.models import User
from django.test import TestCase

from apps.objects.models import Object


class ObjectListSortingTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("s", "s@s.s", "pw")
        Object.objects.create(name="Бета", level=2, status="active", city="Б", creator_id=self.user)
        Object.objects.create(name="Альфа", level=1, status="stopped", city="А", creator_id=self.user)
        Object.objects.create(name="Гамма", level=1, status="active", city="В", creator_id=self.user)

    def _order(self, url):
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        return [o.name for o in resp.context["objects"]]

    def test_default_order(self):
        # дефолт репозитория: level, name
        self.assertEqual(self._order("/objects/"), ["Альфа", "Гамма", "Бета"])

    def test_single_desc(self):
        self.assertEqual(self._order("/objects/?ordering=-name"), ["Гамма", "Бета", "Альфа"])

    def test_single_asc(self):
        self.assertEqual(self._order("/objects/?ordering=name"), ["Альфа", "Бета", "Гамма"])

    def test_multi_level_then_name_desc(self):
        # level asc, внутри уровня name desc
        self.assertEqual(
            self._order("/objects/?ordering=level&ordering=-name"),
            ["Гамма", "Альфа", "Бета"],
        )

    def test_invalid_field_ignored(self):
        self.assertEqual(self._order("/objects/?ordering=creator_id__password"), ["Альфа", "Гамма", "Бета"])


class SortHeaderTagTests(TestCase):
    """Поведение ссылок в заголовках (цикл none->desc->asc->off)."""

    def setUp(self):
        self.user = User.objects.create_user("h", "h@h.h", "pw")
        Object.objects.create(name="A", level=1, creator_id=self.user)

    def test_no_sort_links_to_desc(self):
        html = self.client.get("/objects/").content.decode().replace("&amp;", "&")
        self.assertIn('href="?ordering=-name"', html)

    def test_desc_shows_arrow_and_links_to_asc(self):
        html = self.client.get("/objects/?ordering=-name").content.decode().replace("&amp;", "&")
        self.assertIn("▼", html)
        self.assertIn('href="?ordering=name"', html)

    def test_asc_links_to_removed(self):
        # при возрастании следующий клик убирает сортировку по столбцу
        html = self.client.get("/objects/?ordering=name").content.decode().replace("&amp;", "&")
        self.assertIn("▲", html)
        # ссылка заголовка "Название" не должна содержать ordering для name
        start = html.find("Название")
        segment = html[start - 250:start]
        # в сегменте ссылки этого заголовка не должно быть ordering=name / -name
        self.assertNotIn('ordering=name"', html[start - 250:start + 20])

    def test_other_params_preserved(self):
        html = self.client.get("/objects/?search=abc").content.decode().replace("&amp;", "&")
        # ссылка сортировки сохраняет search
        self.assertIn("search=abc", html)
        self.assertIn("ordering=-name", html)


class RelatedFieldSortingTests(TestCase):
    """Сортировка по связанным колонкам (категория/владелец, класс/вендор)."""

    def setUp(self):
        from apps.categories.models import Category
        from apps.owners.models import OwnerEntity
        from apps.system.models import AutomationClass, AutomatedSystem
        from apps.participants.models import Participant
        self.user = User.objects.create_user("rel", "r@r.r", "pw")

        cat_b = Category.objects.create(name="Бета", level=1, creator_id=self.user)
        cat_a = Category.objects.create(name="Альфа", level=1, creator_id=self.user)
        own_b = OwnerEntity.objects.create(owner_name="Бета-Холдинг")
        own_a = OwnerEntity.objects.create(owner_name="Альфа-Холдинг")
        Object.objects.create(name="O1", level=1, category=cat_b, owner_entity=own_b, creator_id=self.user)
        Object.objects.create(name="O2", level=1, category=cat_a, owner_entity=own_a, creator_id=self.user)

        self.cls_b = AutomationClass.objects.create(level=2, system_class="Бета-класс")
        self.cls_a = AutomationClass.objects.create(level=2, system_class="Альфа-класс")
        self.v_b = Participant.objects.create(participant_name="Бета-вендор")
        self.v_a = Participant.objects.create(participant_name="Альфа-вендор")
        AutomatedSystem.objects.create(autosystem_name="S1", system_class=self.cls_b, vendor=self.v_b, creator_id=self.user)
        AutomatedSystem.objects.create(autosystem_name="S2", system_class=self.cls_a, vendor=self.v_a, creator_id=self.user)

    def test_objects_sort_by_category_name(self):
        resp = self.client.get("/objects/?ordering=category__name")
        self.assertEqual([o.name for o in resp.context["objects"]], ["O2", "O1"])

    def test_objects_sort_by_owner_name_desc(self):
        resp = self.client.get("/objects/?ordering=-owner_entity__owner_name")
        self.assertEqual([o.name for o in resp.context["objects"]], ["O1", "O2"])

    def test_systems_sort_by_class_name(self):
        resp = self.client.get("/system/?ordering=system_class__system_class")
        self.assertEqual([s.autosystem_name for s in resp.context["systems"]], ["S2", "S1"])

    def test_systems_sort_by_vendor_name_desc(self):
        resp = self.client.get("/system/?ordering=-vendor__participant_name")
        self.assertEqual([s.autosystem_name for s in resp.context["systems"]], ["S1", "S2"])

    def test_related_sort_header_links_present(self):
        oh = self.client.get("/objects/").content.decode().replace("&amp;", "&")
        self.assertIn("ordering=-category__name", oh)
        self.assertIn("ordering=-owner_entity__owner_name", oh)
        sh = self.client.get("/system/").content.decode().replace("&amp;", "&")
        self.assertIn("ordering=-system_class__system_class", sh)
        self.assertIn("ordering=-vendor__participant_name", sh)
