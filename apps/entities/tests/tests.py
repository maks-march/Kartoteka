from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from apps.entities.models import Entity


class EntityModelTests(TestCase):
    def test_str_and_defaults(self):
        e = Entity.objects.create(entity_name="Компания")
        self.assertEqual(str(e), "Компания")
        self.assertFalse(e.is_partner)
        self.assertEqual(e.entity_type, "")

    def test_industries_text_property(self):
        e = Entity.objects.create(entity_name="X", industries=["Химия", "Металлургия"])
        self.assertEqual(e.industries_text, "Химия, Металлургия")

    def test_contacts_items_property(self):
        e = Entity.objects.create(entity_name="Y", contacts={"email": "a@b.c"})
        self.assertEqual(e.contacts_items, [("email", "a@b.c")])


class EntityWebEndpointTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="u", password="pw")
        self.entity = Entity.objects.create(entity_name="АйтиКомпания", inn="1234567890")

    def test_list_page(self):
        r = self.client.get("/entities/")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "АйтиКомпания")

    def test_detail_page(self):
        r = self.client.get(f"/entities/{self.entity.pk}/")
        self.assertEqual(r.status_code, 200)

    def test_create_requires_auth(self):
        r = self.client.get("/entities/create/")
        self.assertEqual(r.status_code, 302)

    def test_industry_picker_is_multiselect_without_search(self):
        """Форма: отрасли выбираются множественно (пикер), без поля поиска."""
        from apps.categories.models import Category
        Category.objects.create(name="Химия", level=1)
        Category.objects.create(name="Металлургия", level=1)
        self.client.force_login(self.user)
        h = self.client.get("/entities/create/").content.decode()
        # мультивыбор через пикер, значение пишется в скрытый input с прежним именем
        self.assertIn("industry-picker", h)
        self.assertIn('id="industriesValue"', h)
        self.assertIn('name="industries"', h)
        # пункты — категории 1-го уровня
        self.assertIn('data-name="Химия"', h)
        self.assertIn('data-name="Металлургия"', h)
        # поиска в пикере отраслей быть не должно
        block = h[h.index("industry-picker"):]
        block = block[:block.index("</div></div>") if "</div></div>" in block else len(block)]
        self.assertNotIn("picker-search", block)

    def test_industry_picker_preselects_on_edit(self):
        from apps.categories.models import Category
        Category.objects.create(name="Химия", level=1)
        Category.objects.create(name="Нефтехимия", level=1)
        e = Entity.objects.create(entity_name="Ред", industries=["Химия"])
        self.client.force_login(self.user)
        h = self.client.get(f"/entities/{e.pk}/edit/").content.decode()
        # выбранная отрасль помечена selected, значение предзаполнено
        self.assertIn('class="system-item selected" data-name="Химия"', h)
        self.assertIn('value="Химия"', h)

    def test_authenticated_crud_with_full_fields(self):
        self.client.force_login(self.user)

        r = self.client.get("/entities/create/")
        self.assertEqual(r.status_code, 200)

        r = self.client.post("/entities/create/", {
            "entity_name": "НовыйВендор",
            "inn": "7712345678",
            "entity_type": "vendor",
            "is_partner": "on",
            "registration_date": "2020-01-15",
            "website": "https://example.com",
            "kam_name": "Иванов",
            "kam_phone": "+7 900 000-00-00",
            "contact_person": "Петров",
            "contact_phone": "+7 900 111-11-11",
            "presentation_url": "https://example.com/p.pdf",
            "profile": "Профиль компании",
            "industries": "Химия, Металлургия; Химия",
            "contact_key": ["email", ""],
            "contact_value": ["info@example.com", "пустой ключ"],
            "fin_key": ["revenue"],
            "fin_value": ["1.2 млрд"],
        })
        self.assertEqual(r.status_code, 302)
        e = Entity.objects.get(entity_name="НовыйВендор")
        self.assertEqual(e.inn, "7712345678")
        self.assertEqual(e.entity_type, "vendor")
        self.assertTrue(e.is_partner)
        self.assertEqual(e.website, "https://example.com")
        self.assertEqual(e.industries, ["Химия", "Металлургия", "Химия"])
        self.assertEqual(e.contacts, {"email": "info@example.com"})
        self.assertEqual(e.financial_data, {"revenue": "1.2 млрд"})

        r = self.client.get(f"/entities/{e.pk}/edit/")
        self.assertEqual(r.status_code, 200)

        r = self.client.post(f"/entities/{e.pk}/edit/", {
            "entity_name": "Вендор 2",
            "is_partner": "",  # снимаем галочку
        })
        self.assertEqual(r.status_code, 302)
        e.refresh_from_db()
        self.assertEqual(e.entity_name, "Вендор 2")
        self.assertFalse(e.is_partner)

        r = self.client.post(f"/entities/{e.pk}/delete/")
        self.assertEqual(r.status_code, 302)
        self.assertFalse(Entity.objects.filter(pk=e.pk).exists())

    def test_empty_inn_stored_as_null_allows_multiple(self):
        self.client.force_login(self.user)
        self.client.post("/entities/create/", {"entity_name": "A", "inn": ""})
        self.client.post("/entities/create/", {"entity_name": "B", "inn": ""})
        a = Entity.objects.get(entity_name="A")
        b = Entity.objects.get(entity_name="B")
        self.assertIsNone(a.inn)
        self.assertIsNone(b.inn)


class EntityApiEndpointTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="api", password="pw")
        self.api = APIClient()
        self.entity = Entity.objects.create(entity_name="ApiEntity", entity_type="supplier")

    def test_list_and_detail_public(self):
        r = self.api.get("/api/entities/")
        self.assertEqual(r.status_code, 200)

        r = self.api.get(f"/api/entities/{self.entity.pk}/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["entity_name"], "ApiEntity")
        self.assertEqual(r.data["entity_type_display"], "Поставщик")

    def test_create_requires_auth(self):
        r = self.api.post("/api/entities/", {"entity_name": "X"}, format="json")
        self.assertIn(r.status_code, (401, 403))

    def test_authenticated_api_crud(self):
        self.api.force_authenticate(user=self.user)
        r = self.api.post("/api/entities/", {
            "entity_name": "ApiNew",
            "entity_type": "system_integrator",
            "is_partner": True,
            "industries": ["Химия"],
            "contacts": {"email": "x@y.z"},
        }, format="json")
        self.assertEqual(r.status_code, 201)
        eid = r.data["id"]
        self.assertEqual(r.data["entity_type"], "system_integrator")
        self.assertTrue(r.data["is_partner"])
        self.assertEqual(r.data["industries"], ["Химия"])

        r = self.api.patch(f"/api/entities/{eid}/", {"entity_name": "ApiNew2"}, format="json")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["entity_name"], "ApiNew2")

        r = self.api.delete(f"/api/entities/{eid}/")
        self.assertEqual(r.status_code, 204)
        self.assertFalse(Entity.objects.filter(pk=eid).exists())


class EntityCountsAndViewsTests(TestCase):
    """Счётчики (продукты, связанные системы), карточки, цветные типы, сортировка."""

    def setUp(self):
        from apps.system.models import AutomationClass, AutomationSystem, VendorProduct
        from apps.objects.models import Object, ObjectSystem
        self.user = User.objects.create_user("cv", "cv@x.x", "pw")
        self.cls = AutomationClass.objects.create(level=2, system_class="SCADA")

        # Вендор с двумя продуктами; на одном продукте — система.
        self.vendor = Entity.objects.create(entity_name="ВендорА", entity_type="vendor", is_partner=True)
        self.integ = Entity.objects.create(entity_name="ИнтеграторБ", entity_type="system_integrator")

        self.p1 = VendorProduct.objects.create(product_name="Продукт-1", vendor=self.vendor)
        self.p2 = VendorProduct.objects.create(product_name="Продукт-2", vendor=self.vendor)

        # sys_on_product использует продукт вендора -> связан с вендором через product
        self.sys_prod = AutomationSystem.objects.create(
            autosystem_name="СистемаНаПродукте", system_class=self.cls, product=self.p1, creator_id=self.user)
        # sys_role: интегратор — ИнтеграторБ
        self.sys_role = AutomationSystem.objects.create(
            autosystem_name="СистемаСвязь", system_class=self.cls, creator_id=self.user)
        obj = Object.objects.create(name="Объект", level=1, creator_id=self.user)
        ObjectSystem.objects.create(object=obj, system=self.sys_role, integrator=self.integ)
        # интегратор также интегрирует систему на продукте вендора
        obj2 = Object.objects.create(name="Объект2", level=1, creator_id=self.user)
        ObjectSystem.objects.create(object=obj2, system=self.sys_prod, integrator=self.integ)

    def _entities(self):
        from apps.entities.usecases.entity_usecase import EntityUseCase
        return {e.entity_name: e for e in EntityUseCase().list()}

    def test_products_count(self):
        e = self._entities()
        self.assertEqual(e["ВендорА"].products_count, 2)
        self.assertEqual(e["ИнтеграторБ"].products_count, 0)

    def test_systems_count_via_product(self):
        # Вендор связан с 1 системой (через свой продукт p1)
        self.assertEqual(self._entities()["ВендорА"].systems_count, 1)

    def test_systems_count_via_roles_distinct(self):
        # Интегратор связан с 2 РАЗНЫМИ системами (роль в двух ObjectSystem)
        self.assertEqual(self._entities()["ИнтеграторБ"].systems_count, 2)

    def test_entity_type_tag_class(self):
        self.assertEqual(self.vendor.entity_type_tag_class, "tag-blue")
        self.assertEqual(self.integ.entity_type_tag_class, "tag-ok")

    def test_can_have_products_flag(self):
        self.assertTrue(self.vendor.can_have_products)
        self.assertFalse(self.integ.can_have_products)

    def test_industries_helpers(self):
        e = Entity.objects.create(entity_name="X", industries=["A", "B", "C", "D"])
        self.assertEqual(e.industries_first, "A")
        self.assertEqual(e.industries_first_three, "A, B, C")

    def test_list_page_shows_colored_type_and_counts(self):
        h = self.client.get("/entities/").content.decode()
        self.assertIn("tag-blue", h)          # тип вендора цветной
        self.assertIn("ordering=-systems_count", h)  # колонка/сортировка счётчика систем

    def test_cards_page(self):
        h = self.client.get("/entities/cards/").content.decode()
        self.assertEqual(self.client.get("/entities/cards/").status_code, 200)
        self.assertIn("cards-grid", h)
        self.assertIn("data-href=", h)

    def test_sort_by_is_partner(self):
        from apps.entities.usecases.entity_usecase import EntityUseCase
        # is_partner desc -> партнёр (ВендорА) первым среди этих двух
        names = [e.entity_name for e in EntityUseCase().list(ordering="-is_partner")]
        self.assertLess(names.index("ВендорА"), names.index("ИнтеграторБ"))

    def test_sort_by_systems_count(self):
        from apps.entities.usecases.entity_usecase import EntityUseCase
        names = [e.entity_name for e in EntityUseCase().list(ordering="-systems_count")]
        # ИнтеграторБ (2) должен быть раньше ВендорА (1)
        self.assertLess(names.index("ИнтеграторБ"), names.index("ВендорА"))

    def test_detail_shows_products_block_for_vendor(self):
        h = self.client.get(f"/entities/{self.vendor.pk}/").content.decode()
        self.assertIn("Вендорские продукты", h)
        self.assertIn("Продукт-1", h)

    def test_detail_no_products_block_for_integrator(self):
        h = self.client.get(f"/entities/{self.integ.pk}/").content.decode()
        self.assertNotIn("Вендорские продукты", h)


class DetailSummaryPanelTests(TestCase):
    """Сводная панель справа в детальных карточках (объект/система/участник)."""

    def setUp(self):
        from apps.system.models import AutomationClass, AutomationSystem, VendorProduct
        from apps.objects.models import Object, ObjectSystem
        self.user = User.objects.create_user("sp", "sp@x.x", "pw")
        self.cls = AutomationClass.objects.create(level=2, system_class="SCADA")
        self.vendor = Entity.objects.create(entity_name="ВендорП", entity_type="vendor")
        self.integ = Entity.objects.create(entity_name="ИнтегП", entity_type="system_integrator")
        self.impl = Entity.objects.create(entity_name="ИсполП", entity_type="engineering_company")
        self.product = VendorProduct.objects.create(product_name="ПродуктП", vendor=self.vendor)
        self.system = AutomationSystem.objects.create(
            autosystem_name="СистемаП", system_class=self.cls, product=self.product, creator_id=self.user)
        self.obj = Object.objects.create(name="ОбъектП", level=1, creator_id=self.user)
        ObjectSystem.objects.create(
            object=self.obj, system=self.system, integrator=self.integ, implimentor=self.impl)

    def test_object_summary_panel(self):
        h = self.client.get(f"/objects/{self.obj.pk}/").content.decode()
        self.assertIn("summary-panel", h)
        self.assertIn("Сводка связанности", h)
        # агрегаты из таблицы систем: класс, вендор (через product.vendor),
        # интегратор, исполнитель
        self.assertIn("SCADA", h)
        self.assertIn("Вендоры", h)
        self.assertIn("ВендорП", h)
        self.assertIn("ИнтегП", h)
        self.assertIn("ИсполП", h)

    def test_system_summary_panel(self):
        h = self.client.get(f"/system/{self.system.pk}/").content.decode()
        self.assertIn("summary-panel", h)
        self.assertIn("Сводка связанности", h)
        self.assertIn("Интеграторы", h)
        self.assertIn("ИнтегП", h)
        self.assertIn("ИсполП", h)

    def test_entity_summary_panel(self):
        # у интегратора сводка показывает классы интегрированных систем
        h = self.client.get(f"/entities/{self.integ.pk}/").content.decode()
        self.assertIn("summary-panel", h)
        self.assertIn("Классы интегрированных систем", h)
        self.assertIn("SCADA", h)
        self.assertIn("Интегр. систем", h)

    def test_entity_summary_products_only_for_vendor_types(self):
        hv = self.client.get(f"/entities/{self.vendor.pk}/").content.decode()
        # у вендора в сводке есть метрика продуктов и классы вендорских систем
        self.assertIn("Продуктов", hv)
        self.assertIn("Классы вендорских систем", hv)
        hi = self.client.get(f"/entities/{self.impl.pk}/").content.decode()
        # инжиниринговая компания — без продуктов и вендорских систем в сводке
        self.assertNotIn("Продуктов", hi)
        self.assertNotIn("Классы вендорских систем", hi)


class SummaryLimitTests(TestCase):
    """Сводка обрезает группу до 5 элементов и показывает «ещё N»."""

    def setUp(self):
        from apps.system.models import AutomationClass, AutomationSystem
        from apps.objects.models import Object, ObjectSystem
        self.user = User.objects.create_user("lim", "lim@x.x", "pw")
        self.cls = AutomationClass.objects.create(level=2, system_class="SCADA")
        self.obj = Object.objects.create(name="ОбъектЛ", level=1, creator_id=self.user)
        # 7 разных интеграторов -> в сводке максимум 5 + «ещё 2»
        for i in range(7):
            e = Entity.objects.create(entity_name=f"Инт{i}", entity_type="system_integrator")
            s = AutomationSystem.objects.create(
                autosystem_name=f"С{i}", system_class=self.cls, creator_id=self.user)
            ObjectSystem.objects.create(object=self.obj, system=s, integrator=e)

    def test_object_summary_caps_at_five(self):
        h = self.client.get(f"/objects/{self.obj.pk}/").content.decode()
        # блок сводки
        panel = h.split('summary-panel', 1)[1]
        # в группе «Интеграторы» показано 5 тегов-ссылок + «ещё 2»
        self.assertIn("ещё 2", panel)
        # метрика систем = 7 (не обрезается)
        self.assertIn(">7<", panel)
