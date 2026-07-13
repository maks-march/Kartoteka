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
        Object.objects.create(object_name="Бета", hierarchy_level=2, status="active", city="Б", creator=self.user)
        Object.objects.create(object_name="Альфа", hierarchy_level=1, status="stopped", city="А", creator=self.user)
        Object.objects.create(object_name="Гамма", hierarchy_level=1, status="active", city="В", creator=self.user)

    def _order(self, url):
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        return [o.object_name for o in resp.context["objects"]]

    def test_default_order(self):
        # дефолт репозитория: level, name
        self.assertEqual(self._order("/objects/"), ["Альфа", "Гамма", "Бета"])

    def test_single_desc(self):
        self.assertEqual(self._order("/objects/?ordering=-object_name"), ["Гамма", "Бета", "Альфа"])

    def test_single_asc(self):
        self.assertEqual(self._order("/objects/?ordering=object_name"), ["Альфа", "Бета", "Гамма"])

    def test_multi_level_then_name_desc(self):
        # level asc, внутри уровня name desc
        self.assertEqual(
            self._order("/objects/?ordering=hierarchy_level&ordering=-object_name"),
            ["Гамма", "Альфа", "Бета"],
        )

    def test_invalid_field_ignored(self):
        self.assertEqual(self._order("/objects/?ordering=creator__password"), ["Альфа", "Гамма", "Бета"])


class SortHeaderTagTests(TestCase):
    """Поведение ссылок в заголовках (цикл none->desc->asc->off)."""

    def setUp(self):
        self.user = User.objects.create_user("h", "h@h.h", "pw")
        Object.objects.create(object_name="A", hierarchy_level=1, creator=self.user)

    def test_no_sort_links_to_desc(self):
        html = self.client.get("/objects/").content.decode().replace("&amp;", "&")
        self.assertIn('href="?ordering=-object_name"', html)

    def test_desc_shows_arrow_and_links_to_asc(self):
        html = self.client.get("/objects/?ordering=-object_name").content.decode().replace("&amp;", "&")
        self.assertIn("▼", html)
        self.assertIn('href="?ordering=object_name"', html)

    def test_asc_links_to_removed(self):
        # при возрастании следующий клик убирает сортировку по столбцу
        html = self.client.get("/objects/?ordering=object_name").content.decode().replace("&amp;", "&")
        self.assertIn("▲", html)
        # ссылка заголовка "Название" не должна содержать ordering для name
        start = html.find("Название")
        # в сегменте ссылки этого заголовка не должно быть ordering=object_name / -name
        self.assertNotIn('ordering=object_name"', html[start - 250:start + 20])

    def test_other_params_preserved(self):
        html = self.client.get("/objects/?search=abc").content.decode().replace("&amp;", "&")
        # ссылка сортировки сохраняет search
        self.assertIn("search=abc", html)
        self.assertIn("ordering=-object_name", html)


class RelatedFieldSortingTests(TestCase):
    """Сортировка по связанным колонкам (категория/владелец, класс/вендор)."""

    def setUp(self):
        from apps.categories.models import Category
        from apps.owners.models import OwnerEntity
        from apps.system.models import AutomationClass, AutomationSystem, VendorProduct
        self.user = User.objects.create_user("rel", "r@r.r", "pw")

        cat_b = Category.objects.create(category_name="Бета", object_level=1, creator=self.user)
        cat_a = Category.objects.create(category_name="Альфа", object_level=1, creator=self.user)
        own_b = OwnerEntity.objects.create(owner_name="Бета-Холдинг")
        own_a = OwnerEntity.objects.create(owner_name="Альфа-Холдинг")
        Object.objects.create(object_name="O1", hierarchy_level=1, category=cat_b, owner_entity=own_b, creator=self.user)
        Object.objects.create(object_name="O2", hierarchy_level=1, category=cat_a, owner_entity=own_a, creator=self.user)

        self.cls_b = AutomationClass.objects.create(level=2, system_class="Бета-класс")
        self.cls_a = AutomationClass.objects.create(level=2, system_class="Альфа-класс")
        self.p_b = VendorProduct.objects.create(product_name="Бета-продукт")
        self.p_a = VendorProduct.objects.create(product_name="Альфа-продукт")
        AutomationSystem.objects.create(autosystem_name="S1", system_class=self.cls_b, product=self.p_b, creator=self.user)
        AutomationSystem.objects.create(autosystem_name="S2", system_class=self.cls_a, product=self.p_a, creator=self.user)

    def test_objects_sort_by_category_name(self):
        resp = self.client.get("/objects/?ordering=category__category_name")
        self.assertEqual([o.object_name for o in resp.context["objects"]], ["O2", "O1"])

    def test_objects_sort_by_owner_name_desc(self):
        resp = self.client.get("/objects/?ordering=-owner_entity__owner_name")
        self.assertEqual([o.object_name for o in resp.context["objects"]], ["O1", "O2"])

    def test_systems_sort_by_class_name(self):
        resp = self.client.get("/system/?ordering=system_class__system_class")
        self.assertEqual([s.autosystem_name for s in resp.context["systems"]], ["S2", "S1"])

    def test_systems_sort_by_product_name_desc(self):
        resp = self.client.get("/system/?ordering=-product__product_name")
        self.assertEqual([s.autosystem_name for s in resp.context["systems"]], ["S1", "S2"])

    def test_related_sort_header_links_present(self):
        oh = self.client.get("/objects/").content.decode().replace("&amp;", "&")
        self.assertIn("ordering=-category__category_name", oh)
        self.assertIn("ordering=-owner_entity__owner_name", oh)
        sh = self.client.get("/system/").content.decode().replace("&amp;", "&")
        self.assertIn("ordering=-system_class__system_class", sh)
        self.assertIn("ordering=-product__product_name", sh)


class ViewModeAndNavTests(TestCase):
    def setUp(self):
        from apps.system.models import AutomationClass, AutomationSystem
        self.user = User.objects.create_user("vm", "vm@x.x", "pw")
        Object.objects.create(object_name="Объект A", hierarchy_level=1, status="active", city="Омск", creator=self.user)
        cls = AutomationClass.objects.create(level=2, system_class="SCADA")
        AutomationSystem.objects.create(autosystem_name="Sys A", system_class=cls, creator=self.user)

    def test_object_cards_page(self):
        r = self.client.get("/objects/cards/")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "cards-grid")
        self.assertContains(r, "entity-card")
        self.assertContains(r, "Объект A")

    def test_system_cards_page(self):
        r = self.client.get("/system/cards/")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "cards-grid")
        self.assertContains(r, "Sys A")

    def test_cards_respect_filters(self):
        Object.objects.create(object_name="Другой", hierarchy_level=1, status="stopped", creator=self.user)
        r = self.client.get("/objects/cards/?search=Объект")
        self.assertContains(r, "Объект A")
        # "Другой" не должен попасть в сетку карточек
        grid = r.content.decode().split('cards-grid', 1)[1]
        self.assertNotIn("Другой", grid)

    def test_nav_has_dropdown_and_renamed_owners(self):
        r = self.client.get("/objects/")
        self.assertContains(r, "nav-dropdown")
        self.assertContains(r, "Владельцы")
        self.assertNotContains(r, "Юр. лица")
        self.assertContains(r, "Карточки")


class CardCountsTests(TestCase):
    def setUp(self):
        from apps.objects.models import Object, ObjectSystem
        from apps.system.models import AutomationClass, AutomationSystem
        self.user = User.objects.create_user("cc", "cc@x.x", "pw")
        self.o = Object.objects.create(object_name="Объект A", hierarchy_level=1, status="active", creator=self.user)
        self.o2 = Object.objects.create(object_name="Объект B", hierarchy_level=1, status="active", creator=self.user)
        cls = AutomationClass.objects.create(level=2, system_class="SCADA")
        self.s1 = AutomationSystem.objects.create(autosystem_name="S1", system_class=cls, creator=self.user)
        self.s2 = AutomationSystem.objects.create(autosystem_name="S2", system_class=cls, creator=self.user)
        ObjectSystem.objects.create(object=self.o, system=self.s1)
        ObjectSystem.objects.create(object=self.o, system=self.s2)
        ObjectSystem.objects.create(object=self.o2, system=self.s1)

    def test_object_systems_count(self):
        from apps.objects.usecases.object_usecase import ObjectUseCase
        counts = {o.object_name: o.systems_count for o in ObjectUseCase().list()}
        self.assertEqual(counts["Объект A"], 2)
        self.assertEqual(counts["Объект B"], 1)

    def test_system_objects_count(self):
        from apps.system.usecases.system_usecase import SystemUseCase
        counts = {s.autosystem_name: s.objects_count for s in SystemUseCase().list()}
        self.assertEqual(counts["S1"], 2)
        self.assertEqual(counts["S2"], 1)

    def test_cards_render_counts_and_datahref(self):
        ho = self.client.get("/objects/cards/").content.decode()
        self.assertIn("data-href=", ho)
        self.assertRegex(ho, r'Систем</span><span class="v">\d+')
        hs = self.client.get("/system/cards/").content.decode()
        self.assertIn("data-href=", hs)
        self.assertRegex(hs, r'Объектов</span><span class="v">\d+')


class CountSortingTests(TestCase):
    """Сортировка по количеству подключённых сущностей (systems_count / objects_count)."""

    def setUp(self):
        from apps.objects.models import Object, ObjectSystem
        from apps.system.models import AutomationClass, AutomationSystem
        self.user = User.objects.create_user("cnt", "cnt@x.x", "pw")
        cls = AutomationClass.objects.create(level=2, system_class="SCADA")
        self.a = Object.objects.create(object_name="A", hierarchy_level=1, status="active", creator=self.user)  # 0 систем
        self.b = Object.objects.create(object_name="B", hierarchy_level=1, status="active", creator=self.user)  # 2
        self.c = Object.objects.create(object_name="C", hierarchy_level=1, status="active", creator=self.user)  # 1
        self.s1 = AutomationSystem.objects.create(autosystem_name="S1", system_class=cls, creator=self.user)  # 2 объекта
        self.s2 = AutomationSystem.objects.create(autosystem_name="S2", system_class=cls, creator=self.user)  # 1 объект
        ObjectSystem.objects.create(object=self.b, system=self.s1)
        ObjectSystem.objects.create(object=self.b, system=self.s2)
        ObjectSystem.objects.create(object=self.c, system=self.s1)

    def _objs(self, url):
        return [o.object_name for o in self.client.get(url).context["objects"]]

    def _syss(self, url):
        return [s.autosystem_name for s in self.client.get(url).context["systems"]]

    def test_objects_sort_by_systems_count_asc(self):
        self.assertEqual(self._objs("/objects/?ordering=systems_count"), ["A", "C", "B"])

    def test_objects_sort_by_systems_count_desc(self):
        self.assertEqual(self._objs("/objects/?ordering=-systems_count"), ["B", "C", "A"])

    def test_systems_sort_by_objects_count_desc(self):
        self.assertEqual(self._syss("/system/?ordering=-objects_count"), ["S1", "S2"])

    def test_count_headers_are_clickable(self):
        ho = self.client.get("/objects/").content.decode().replace("&amp;", "&")
        self.assertIn("ordering=-systems_count", ho)
        hs = self.client.get("/system/").content.decode().replace("&amp;", "&")
        self.assertIn("ordering=-objects_count", hs)
