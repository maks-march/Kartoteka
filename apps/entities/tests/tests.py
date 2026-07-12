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
        Category.objects.create(category_name="Химия", object_level=1)
        Category.objects.create(category_name="Металлургия", object_level=1)
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
        Category.objects.create(category_name="Химия", object_level=1)
        Category.objects.create(category_name="Нефтехимия", object_level=1)
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
        from apps.entities.models import VendorProfile
        self.vendor = Entity.objects.create(entity_name="ВендорА", entity_type="vendor", is_partner=True)
        self.integ = Entity.objects.create(entity_name="ИнтеграторБ", entity_type="system_integrator")

        self.vendor_profile = VendorProfile.objects.create(entity=self.vendor)
        self.p1 = VendorProduct.objects.create(product_name="Продукт-1", vendor=self.vendor_profile)
        self.p2 = VendorProduct.objects.create(product_name="Продукт-2", vendor=self.vendor_profile)

        # sys_on_product использует продукт вендора -> связан с вендором через product
        self.sys_prod = AutomationSystem.objects.create(
            autosystem_name="СистемаНаПродукте", system_class=self.cls, product=self.p1, creator_id=self.user)
        # sys_role: интегратор — ИнтеграторБ
        self.sys_role = AutomationSystem.objects.create(
            autosystem_name="СистемаСвязь", system_class=self.cls, creator_id=self.user)
        obj = Object.objects.create(object_name="Объект", hierarchy_level=1, creator_id=self.user)
        ObjectSystem.objects.create(object=obj, system=self.sys_role, integrator=self.integ)
        # интегратор также интегрирует систему на продукте вендора
        obj2 = Object.objects.create(object_name="Объект2", hierarchy_level=1, creator_id=self.user)
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
        from apps.entities.models import VendorProfile
        self.vendor = Entity.objects.create(entity_name="ВендорП", entity_type="vendor")
        self.integ = Entity.objects.create(entity_name="ИнтегП", entity_type="system_integrator")
        self.impl = Entity.objects.create(entity_name="ИсполП", entity_type="engineering_company")
        self.vendor_profile = VendorProfile.objects.create(entity=self.vendor)
        self.product = VendorProduct.objects.create(product_name="ПродуктП", vendor=self.vendor_profile)
        self.system = AutomationSystem.objects.create(
            autosystem_name="СистемаП", system_class=self.cls, product=self.product, creator_id=self.user)
        self.obj = Object.objects.create(object_name="ОбъектП", hierarchy_level=1, creator_id=self.user)
        ObjectSystem.objects.create(
            object=self.obj, system=self.system, integrator=self.integ, implementor=self.impl)

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
        self.obj = Object.objects.create(object_name="ОбъектЛ", hierarchy_level=1, creator_id=self.user)
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


class EntityTypingProfilesTests(TestCase):
    """Типизация Entity через профили: авто-создание/удаление и данные инж. компании."""

    def setUp(self):
        from apps.system.models import AutomationClass
        from apps.objects.models import Object
        self.user = User.objects.create_user("typ", "typ@x.x", "pw")
        self.client.force_login(self.user)
        self.cls = AutomationClass.objects.create(level=3, system_class="MES")
        self.obj = Object.objects.create(object_name="ЗаводТ", hierarchy_level=1, region="Урал", creator_id=self.user)

    def _uc(self):
        from apps.entities.usecases.entity_usecase import EntityUseCase
        return EntityUseCase()

    def test_vendor_profile_autocreated_and_removed(self):
        from apps.entities.models import VendorProfile
        e = self._uc().create(entity_name="В1", entity_type="vendor")
        self.assertTrue(VendorProfile.objects.filter(entity=e).exists())
        # смена типа на интегратора удаляет пустой профиль вендора
        self._uc().update(e.pk, entity_name="В1", entity_type="system_integrator")
        self.assertFalse(VendorProfile.objects.filter(entity=e).exists())

    def test_vendor_profile_kept_if_has_products(self):
        from apps.entities.models import VendorProfile
        from apps.system.models import VendorProduct
        e = self._uc().create(entity_name="В2", entity_type="vendor")
        prof = VendorProfile.objects.get(entity=e)
        VendorProduct.objects.create(product_name="P", vendor=prof)
        # смена типа НЕ удаляет профиль, пока есть продукты
        self._uc().update(e.pk, entity_name="В2", entity_type="supplier")
        self.assertTrue(VendorProfile.objects.filter(entity=e).exists())

    def test_engineering_profile_autocreated(self):
        from apps.entities.models import EngineeringCompanyProfile
        e = self._uc().create(entity_name="ИК", entity_type="engineering_company")
        self.assertTrue(EngineeringCompanyProfile.objects.filter(entity=e).exists())

    def test_supplier_profile_autocreated_and_removed(self):
        from apps.entities.models import SupplierProfile
        e = self._uc().create(entity_name="Пост1", entity_type="supplier")
        self.assertTrue(SupplierProfile.objects.filter(entity=e).exists())
        # смена типа удаляет профиль поставщика (связь неэксклюзивная)
        self._uc().update(e.pk, entity_name="Пост1", entity_type="system_integrator")
        self.assertFalse(SupplierProfile.objects.filter(entity=e).exists())

    def test_supplier_products_are_multiple_and_independent_of_vendor(self):
        from apps.entities.models import SupplierProfile, VendorProfile
        from apps.system.models import VendorProduct
        # продукт с автором-вендором
        vend = self._uc().create(entity_name="ВендорА", entity_type="vendor")
        p1 = VendorProduct.objects.create(product_name="Прод1", vendor=VendorProfile.objects.get(entity=vend))
        p2 = VendorProduct.objects.create(product_name="Прод2")
        # поставщик поставляет оба (в т.ч. чужой продукт p1)
        sup = self._uc().create(entity_name="ПоставщикА", entity_type="supplier")
        self._uc().save_supplier_products(sup, product_ids=[p1.pk, p2.pk])
        prof = SupplierProfile.objects.get(entity=sup)
        self.assertEqual(set(prof.products.values_list("pk", flat=True)), {p1.pk, p2.pk})
        # авторство p1 не изменилось (остался у вендора)
        p1.refresh_from_db()
        self.assertEqual(p1.vendor.entity_id, vend.pk)
        # один продукт может поставляться несколькими поставщиками
        sup2 = self._uc().create(entity_name="ПоставщикБ", entity_type="supplier")
        self._uc().save_supplier_products(sup2, product_ids=[p1.pk])
        self.assertEqual(set(p1.suppliers.values_list("entity__entity_name", flat=True)),
                         {"ПоставщикА", "ПоставщикБ"})

    def test_web_supplier_saves_products(self):
        from apps.entities.models import Entity, SupplierProfile
        from apps.system.models import VendorProduct
        prod = VendorProduct.objects.create(product_name="ПродФорма")
        r = self.client.post("/entities/create/", {
            "entity_name": "ПостФорма", "entity_type": "supplier",
            "supplier_products": [str(prod.pk)],
        })
        self.assertEqual(r.status_code, 302)
        e = Entity.objects.get(entity_name="ПостФорма")
        self.assertEqual(list(e.supplier_profile.products.values_list("pk", flat=True)), [prod.pk])

    def test_form_shows_supplier_block(self):
        from apps.system.models import VendorProduct
        VendorProduct.objects.create(product_name="ПродДляБлока")
        h = self.client.get("/entities/create/").content.decode()
        self.assertIn('data-for="supplier full_cycle_vendor"', h)
        self.assertIn('id="supplierProductsPicker"', h)
        self.assertIn('name="supplier_products"', h)

    def test_full_cycle_vendor_has_all_three_profiles(self):
        """Вендор полного цикла = vendor + supplier + engineering + dedicated full_cycle_profile."""
        from apps.entities.models import (
            VendorProfile, SupplierProfile, EngineeringCompanyProfile, FullCycleVendorProfile,
        )
        e = self._uc().create(entity_name="ФПЦ", entity_type="full_cycle_vendor")
        self.assertTrue(VendorProfile.objects.filter(entity=e).exists())
        self.assertTrue(SupplierProfile.objects.filter(entity=e).exists())
        self.assertTrue(EngineeringCompanyProfile.objects.filter(entity=e).exists())
        self.assertTrue(FullCycleVendorProfile.objects.filter(entity=e).exists())
        # признаки типа охватывают full_cycle_vendor
        self.assertTrue(e.is_vendor_type)
        self.assertTrue(e.is_supplier_type)
        self.assertTrue(e.is_engineering_type)
        # dedicated profile only via direct entity_type check
        self.assertEqual(e.entity_type, "full_cycle_vendor")

    def test_full_cycle_vendor_saves_supplier_and_engineering(self):
        from apps.entities.models import Entity
        from apps.system.models import VendorProduct
        prod = VendorProduct.objects.create(product_name="ФПЦпрод")
        r = self.client.post("/entities/create/", {
            "entity_name": "ФПЦФорма", "entity_type": "full_cycle_vendor",
            "supplier_products": [str(prod.pk)],
            "region": "Урал",
            "comp_class": [str(self.cls.pk)], "comp_industry": ["Химия"],
        })
        self.assertEqual(r.status_code, 302)
        e = Entity.objects.get(entity_name="ФПЦФорма")
        # поставщик
        self.assertEqual(list(e.supplier_profile.products.values_list("pk", flat=True)), [prod.pk])
        # инж. компания (всегда для full_cycle_vendor)
        self.assertEqual(e.engineering_profile.region, "Урал")
        self.assertEqual(e.engineering_profile.function_competencies.count(), 1)
        # dedicated full cycle profile (новый dedicated)
        from apps.entities.models import FullCycleVendorProfile
        self.assertTrue(FullCycleVendorProfile.objects.filter(entity=e).exists())
        fcp = e.full_cycle_profile
        self.assertEqual(fcp.region, "Урал")
        self.assertEqual(fcp.function_competencies.count(), 1)
        self.assertEqual(fcp.function_competencies.first().industry, "Химия")

    def test_system_integrator_profile_autocreated_and_removed(self):
        from apps.entities.models import SystemIntegratorProfile
        e = self._uc().create(entity_name="СИ1", entity_type="system_integrator")
        self.assertTrue(SystemIntegratorProfile.objects.filter(entity=e).exists())
        self._uc().update(e.pk, entity_name="СИ1", entity_type="supplier")
        self.assertFalse(SystemIntegratorProfile.objects.filter(entity=e).exists())

    def test_system_integrator_partners_and_owner(self):
        from apps.entities.models import SystemIntegratorProfile, VendorProfile
        from apps.owners.models import OwnerEntity
        owner = OwnerEntity.objects.create(owner_name="Холдинг")
        v1 = self._uc().create(entity_name="Вен1", entity_type="vendor")
        v2 = self._uc().create(entity_name="Вен2", entity_type="full_cycle_vendor")
        vp1 = VendorProfile.objects.get(entity=v1)
        vp2 = VendorProfile.objects.get(entity=v2)
        si = self._uc().create(entity_name="Интегр", entity_type="system_integrator")
        self._uc().save_system_integrator_profile(
            si, managing_owner_id=owner.pk, vendor_partner_ids=[vp1.pk, vp2.pk])
        prof = SystemIntegratorProfile.objects.get(entity=si)
        self.assertEqual(prof.managing_owner_id, owner.pk)
        self.assertEqual(set(prof.vendor_partners.values_list("pk", flat=True)), {vp1.pk, vp2.pk})
        # «карта партнёров»: у вендора виден интегратор через reverse M2M
        self.assertIn("Интегр", vp1.partner_integrators.values_list("entity__entity_name", flat=True))
        # внутренний интегратор виден у OwnerEntity
        self.assertIn(si.pk, owner.internal_integrators.values_list("entity_id", flat=True))

    def test_web_system_integrator_saves_profile(self):
        from apps.entities.models import Entity, VendorProfile
        from apps.owners.models import OwnerEntity
        owner = OwnerEntity.objects.create(owner_name="ХолдингФорма")
        v = self._uc().create(entity_name="ВенФорма", entity_type="vendor")
        vp = VendorProfile.objects.get(entity=v)
        r = self.client.post("/entities/create/", {
            "entity_name": "ИнтегрФорма", "entity_type": "system_integrator",
            "managing_owner": str(owner.pk),
            "vendor_partners": [str(vp.pk)],
        })
        self.assertEqual(r.status_code, 302)
        e = Entity.objects.get(entity_name="ИнтегрФорма")
        sip = e.system_integrator_profile
        self.assertEqual(sip.managing_owner_id, owner.pk)
        self.assertEqual(list(sip.vendor_partners.values_list("pk", flat=True)), [vp.pk])

    def test_form_shows_integrator_block(self):
        from apps.owners.models import OwnerEntity
        OwnerEntity.objects.create(owner_name="Х")
        v = self._uc().create(entity_name="ВенДляБлока", entity_type="vendor")
        h = self.client.get("/entities/create/").content.decode()
        self.assertIn('data-for="system_integrator"', h)
        self.assertIn('name="managing_owner"', h)
        self.assertIn('id="vendorPartnersPicker"', h)
        self.assertIn('name="vendor_partners"', h)

    def test_product_only_for_vendor_types(self):
        from django.core.exceptions import ValidationError
        from apps.system.usecases.vendor_product_usecase import VendorProductUseCase
        integ = self._uc().create(entity_name="Инт", entity_type="system_integrator")
        with self.assertRaises(ValidationError):
            VendorProductUseCase().create(product_name="X", vendor=integ.pk)

    def test_web_create_engineering_with_profile_fields(self):
        from apps.entities.models import Entity, VendorProfile
        from apps.system.models import VendorProduct
        vend = self._uc().create(entity_name="ВендорПрод", entity_type="vendor")
        product = VendorProduct.objects.create(product_name="Prod1", vendor=VendorProfile.objects.get(entity=vend))
        r = self.client.post("/entities/create/", {
            "entity_name": "ИнжКомп",
            "entity_type": "engineering_company",
            "region": "Урал",
            "resident_object": str(self.obj.pk),
            "product_competencies": [str(product.pk)],
            "comp_class": [str(self.cls.pk), ""],
            "comp_industry": ["Нефтехимия", "пропуск-без-класса"],
        })
        self.assertEqual(r.status_code, 302)
        e = Entity.objects.get(entity_name="ИнжКомп")
        prof = e.engineering_profile
        self.assertEqual(prof.region, "Урал")
        self.assertEqual(prof.resident_object_id, self.obj.pk)
        self.assertEqual(list(prof.product_competencies.values_list("pk", flat=True)), [product.pk])
        # одна валидная компетенция (вторая без класса — отброшена)
        self.assertEqual(prof.function_competencies.count(), 1)
        fc = prof.function_competencies.first()
        self.assertEqual(fc.system_class_id, self.cls.pk)
        self.assertEqual(fc.industry, "Нефтехимия")

    def test_web_vendor_assigns_free_products(self):
        """Вендор через форму назначает свободные продукты; при снятии — освобождает."""
        from apps.system.models import VendorProduct
        from apps.entities.models import Entity, VendorProfile
        # свободный продукт (без вендора)
        free = VendorProduct.objects.create(product_name="Свободный")
        r = self.client.post("/entities/create/", {
            "entity_name": "ВендорФорма", "entity_type": "vendor",
            "vendor_products": [str(free.pk)],
        })
        self.assertEqual(r.status_code, 302)
        e = Entity.objects.get(entity_name="ВендорФорма")
        free.refresh_from_db()
        self.assertEqual(free.vendor, VendorProfile.objects.get(entity=e))
        # правка: снимаем продукт -> освобождается
        r = self.client.post(f"/entities/{e.pk}/edit/", {
            "entity_name": "ВендорФорма", "entity_type": "vendor",
            "vendor_products": [],
        })
        self.assertEqual(r.status_code, 302)
        free.refresh_from_db()
        self.assertIsNone(free.vendor)

    def test_vendorless_products_in_context(self):
        """В блоке вендора показаны только продукты без вендора."""
        from apps.system.models import VendorProduct
        from apps.entities.models import VendorProfile
        VendorProduct.objects.create(product_name="Свободный1")
        other = Entity.objects.create(entity_name="ДругойВендор", entity_type="vendor")
        VendorProduct.objects.create(product_name="Занятый", vendor=VendorProfile.objects.create(entity=other))
        h = self.client.get("/entities/create/").content.decode()
        # вырезаем только блок пикера вендорских продуктов
        start = h.index('id="vendorProductsPicker"')
        block = h[start:h.index("vendorProductsInputs")]
        self.assertIn("Свободный1", block)
        self.assertNotIn("Занятый", block)
        # новый формат: капсульный пикер с группами и автопоиском
        self.assertIn("capsule-picker", h)
        self.assertIn('data-group="free"', block)
        self.assertIn("picker-chips", block)

    def test_vendor_own_products_shown_first_and_selected(self):
        """В режиме правки продукты этого вендора идут первыми и предвыбраны."""
        from apps.system.models import VendorProduct
        from apps.entities.models import VendorProfile
        e = self._uc().create(entity_name="ВендорСвои", entity_type="vendor")
        VendorProduct.objects.create(product_name="Мой продукт", vendor=VendorProfile.objects.get(entity=e))
        VendorProduct.objects.create(product_name="Свободный2")
        h = self.client.get(f"/entities/{e.pk}/edit/").content.decode()
        block = h[h.index('id="vendorProductsPicker"'):h.index("vendorProductsInputs")]
        self.assertIn('data-group="own"', block)
        # «свои» идут раньше «свободных» в разметке
        self.assertLess(block.index("Мой продукт"), block.index("Свободный2"))

    def test_form_shows_engineering_section(self):
        from apps.system.models import VendorProduct
        VendorProduct.objects.create(product_name="Продукт для блока")  # чтобы блок вендора отрисовался
        h = self.client.get("/entities/create/").content.decode()
        # блок инж. компании (через data-for) + его поля
        self.assertIn('data-for="engineering_company full_cycle_vendor"', h)
        self.assertIn('name="region"', h)
        self.assertIn('name="resident_object"', h)
        self.assertIn('id="residentObjectPicker"', h)
        self.assertIn('id="competencyAddBtn"', h)
        # combobox-данные для класса/индустрии
        self.assertIn('id="competencyClassesData"', h)
        self.assertIn('id="competencyIndustriesData"', h)
        # блок вендора со свободными продуктами
        self.assertIn('data-for="vendor full_cycle_vendor"', h)
        self.assertIn('name="vendor_products"', h)
        # переключатель партнёрства в нашем стиле
        self.assertIn('id="partnerToggle"', h)

    def test_vendor_block_empty_when_no_products(self):
        """Если продуктов нет — пикер и пояснение не показываются (пустое поле)."""
        from apps.system.models import VendorProduct
        VendorProduct.objects.all().delete()
        h = self.client.get("/entities/create/").content.decode()
        self.assertNotIn('id="vendorProductsPicker"', h)
        self.assertNotIn("затем свободные", h)

    def test_detail_shows_engineering_block(self):
        e = self._uc().create(entity_name="ИК2", entity_type="engineering_company")
        self._uc().save_engineering_profile(
            e, region="Сибирь", resident_object_id=self.obj.pk,
            product_ids=[], competencies=[(self.cls.pk, "Химия")])
        h = self.client.get(f"/entities/{e.pk}/").content.decode()
        self.assertIn("Инжиниринговая компания", h)
        self.assertIn("Сибирь", h)
        self.assertIn("Химия", h)


class EngineeringProfileAPITests(TestCase):
    """REST API профиля инжиниринговой компании."""

    def setUp(self):
        from rest_framework.test import APIClient
        from apps.system.models import AutomationClass, VendorProduct
        from apps.objects.models import Object
        from apps.entities.models import VendorProfile
        from apps.entities.usecases.entity_usecase import EntityUseCase

        self.user = User.objects.create_user("api", "api@x.x", "pw")
        self.api = APIClient()
        self.cls = AutomationClass.objects.create(level=3, system_class="MES")
        self.obj = Object.objects.create(object_name="ОбъектAPI", hierarchy_level=1, creator_id=self.user)
        vend = EntityUseCase().create(entity_name="ВендAPI", entity_type="vendor")
        self.product = VendorProduct.objects.create(
            product_name="ProdAPI", vendor=VendorProfile.objects.get(entity=vend))
        self.eng = EntityUseCase().create(entity_name="ИнжAPI", entity_type="engineering_company")

    def test_put_and_get_engineering_profile(self):
        self.api.force_authenticate(user=self.user)
        r = self.api.put(f"/api/entities/{self.eng.pk}/engineering-profile/", {
            "region": "Урал",
            "resident_object": self.obj.pk,
            "product_competencies": [self.product.pk],
            "function_competencies": [{"system_class": self.cls.pk, "industry": "Нефтехимия"}],
        }, format="json")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["region"], "Урал")
        self.assertEqual(r.data["resident_object"], self.obj.pk)
        self.assertEqual(r.data["product_competencies"], [self.product.pk])
        self.assertEqual(len(r.data["function_competencies"]), 1)
        self.assertEqual(r.data["function_competencies"][0]["industry"], "Нефтехимия")

        # GET доступен без авторизации
        r = self.api.get(f"/api/entities/{self.eng.pk}/engineering-profile/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["region"], "Урал")

    def test_put_rejected_for_non_engineering(self):
        from apps.entities.usecases.entity_usecase import EntityUseCase
        integ = EntityUseCase().create(entity_name="ИнтAPI", entity_type="system_integrator")
        self.api.force_authenticate(user=self.user)
        r = self.api.put(f"/api/entities/{integ.pk}/engineering-profile/",
                         {"region": "X"}, format="json")
        self.assertEqual(r.status_code, 400)

    def test_get_404_when_no_profile(self):
        from apps.entities.usecases.entity_usecase import EntityUseCase
        sup = EntityUseCase().create(entity_name="ПостAPI", entity_type="supplier")
        r = self.api.get(f"/api/entities/{sup.pk}/engineering-profile/")
        self.assertEqual(r.status_code, 404)

    def test_entity_detail_api_includes_profile(self):
        from apps.entities.usecases.entity_usecase import EntityUseCase
        EntityUseCase().save_engineering_profile(
            self.eng, region="Сибирь", resident_object_id=None,
            product_ids=[self.product.pk], competencies=[(self.cls.pk, "Химия")])
        r = self.api.get(f"/api/entities/{self.eng.pk}/")
        self.assertEqual(r.status_code, 200)
        self.assertIsNotNone(r.data["engineering_profile"])
        self.assertEqual(r.data["engineering_profile"]["region"], "Сибирь")

    def test_put_requires_auth(self):
        r = self.api.put(f"/api/entities/{self.eng.pk}/engineering-profile/",
                         {"region": "X"}, format="json")
        self.assertIn(r.status_code, (401, 403))
