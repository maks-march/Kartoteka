"""Тесты приложения участников рынка: модели, HTML/API эндпоинты, профили типов."""
from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from apps.entities.models import Entity


class EntityModelTests(TestCase):
    """Тесты модели участника: строковое представление и свойства."""
    def test_str_and_defaults(self):
        """Строковое представление и значения по умолчанию."""
        e = Entity.objects.create(entity_name="Компания")
        self.assertEqual(str(e), "Компания")
        self.assertFalse(e.is_partner)
        self.assertEqual(e.entity_type, "")

    def test_industries_computed_from_vendor_products(self):
        """Отрасли участника вычисляются из отраслей его продуктов (вендор)."""
        from apps.categories.models import Category
        from apps.entities.models import VendorProfile
        from apps.system.models import VendorProduct
        from apps.entities.usecases.entity_usecase import EntityUseCase
        cat = Category.objects.create(category_name="Химия", object_level=1)
        e = EntityUseCase().create(entity_name="X", entity_type="vendor")
        vp = VendorProfile.objects.get(entity=e)
        prod = VendorProduct.objects.create(product_name="P", vendor=vp)
        prod.industries.set([cat])
        self.assertEqual(e.industries_text, "Химия")
        self.assertIn(cat, list(e.industries))

    def test_contacts_items_property(self):
        """Свойство contacts_items возвращает пары контактов."""
        e = Entity.objects.create(entity_name="Y", contacts={"email": "a@b.c"})
        self.assertEqual(e.contacts_items, [("email", "a@b.c")])


class EntityWebEndpointTests(TestCase):
    """Тесты HTML-эндпоинтов участников (список, детали, CRUD, форма)."""
    def setUp(self):
        """Готовит тестовые данные перед каждым тестом."""
        self.user = User.objects.create_user(username="u", password="pw")
        self.entity = Entity.objects.create(entity_name="АйтиКомпания", inn="1234567890")

    def test_list_page(self):
        """Страница списка участников открывается."""
        r = self.client.get("/entities/")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "АйтиКомпания")

    def test_detail_page(self):
        """Страница деталей участника открывается."""
        r = self.client.get(f"/entities/{self.entity.pk}/", follow=True)
        self.assertEqual(r.status_code, 200)

    def test_create_requires_auth(self):
        """Создание участника требует авторизации."""
        r = self.client.get("/entities/create/")
        self.assertEqual(r.status_code, 302)

    def test_industries_not_editable_in_form(self):
        """Форма участника не содержит ручного ввода отраслей — они вычисляются."""
        self.client.force_login(self.user)
        h = self.client.get("/entities/create/").content.decode()
        # прежнего пикера/поля отраслей быть не должно
        self.assertNotIn("industry-picker", h)
        self.assertNotIn('id="industriesValue"', h)
        # есть пояснение об автоматическом определении отраслей
        self.assertIn("Определяются автоматически", h)

    def test_authenticated_crud_with_full_fields(self):
        """CRUD участника со всеми полями (авторизованный)."""
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
        """Пустой ИНН хранится как NULL и допускает несколько записей."""
        self.client.force_login(self.user)
        self.client.post("/entities/create/", {"entity_name": "A", "inn": ""})
        self.client.post("/entities/create/", {"entity_name": "B", "inn": ""})
        a = Entity.objects.get(entity_name="A")
        b = Entity.objects.get(entity_name="B")
        self.assertIsNone(a.inn)
        self.assertIsNone(b.inn)


class EntityApiEndpointTests(TestCase):
    """Тесты REST API участников (список, детали, CRUD)."""
    def setUp(self):
        """Готовит тестовые данные перед каждым тестом."""
        self.user = User.objects.create_user(username="api", password="pw")
        self.api = APIClient()
        self.entity = Entity.objects.create(entity_name="ApiEntity", entity_type="supplier")

    def test_list_and_detail_public(self):
        """Список и детали участников доступны без авторизации (API)."""
        r = self.api.get("/api/entities/")
        self.assertEqual(r.status_code, 200)

        r = self.api.get(f"/api/entities/{self.entity.pk}/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["entity_name"], "ApiEntity")
        self.assertEqual(r.data["entity_type_display"], "Поставщик")

    def test_create_requires_auth(self):
        """Создание участника требует авторизации."""
        r = self.api.post("/api/entities/", {"entity_name": "X"}, format="json")
        self.assertIn(r.status_code, (401, 403))

    def test_authenticated_api_crud(self):
        """Полный CRUD участника через API."""
        self.api.force_authenticate(user=self.user)
        r = self.api.post("/api/entities/", {
            "entity_name": "ApiNew",
            "entity_type": "system_integrator",
            "is_partner": True,
            "contacts": {"email": "x@y.z"},
        }, format="json")
        self.assertEqual(r.status_code, 201)
        eid = r.data["id"]
        self.assertEqual(r.data["entity_type"], "system_integrator")
        self.assertTrue(r.data["is_partner"])
        # отрасли вычисляются из связей — у нового интегратора их нет
        self.assertEqual(r.data["industries"], [])

        r = self.api.patch(f"/api/entities/{eid}/", {"entity_name": "ApiNew2"}, format="json")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["entity_name"], "ApiNew2")

        r = self.api.delete(f"/api/entities/{eid}/")
        self.assertEqual(r.status_code, 204)
        self.assertFalse(Entity.objects.filter(pk=eid).exists())


class EntityCountsAndViewsTests(TestCase):
    """Счётчики (продукты, связанные системы), карточки, цветные типы, сортировка."""

    def setUp(self):
        """Готовит тестовые данные перед каждым тестом."""
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
            autosystem_name="СистемаНаПродукте", system_class=self.cls, product=self.p1, creator=self.user)
        # sys_role: интегратор — ИнтеграторБ
        self.sys_role = AutomationSystem.objects.create(
            autosystem_name="СистемаСвязь", system_class=self.cls, creator=self.user)
        obj = Object.objects.create(object_name="Объект", hierarchy_level=1, creator=self.user)
        ObjectSystem.objects.create(object=obj, system=self.sys_role, implementor=self.integ)
        # интегратор также интегрирует систему на продукте вендора
        obj2 = Object.objects.create(object_name="Объект2", hierarchy_level=1, creator=self.user)
        ObjectSystem.objects.create(object=obj2, system=self.sys_prod, implementor=self.integ)

    def _entities(self):
        """Возвращает участников по имени из use case (вспомогательная)."""
        from apps.entities.usecases.entity_usecase import EntityUseCase
        return {e.entity_name: e for e in EntityUseCase().list()}

    def test_products_count(self):
        """Счётчик продуктов участника-вендора верен."""
        e = self._entities()
        self.assertEqual(e["ВендорА"].products_count, 2)
        self.assertEqual(e["ИнтеграторБ"].products_count, 0)

    def test_systems_count_via_product(self):
        # Вендор связан с 1 системой (через свой продукт p1)
        """Счётчик систем через продукты вендора верен."""
        self.assertEqual(self._entities()["ВендорА"].systems_count, 1)

    def test_systems_count_via_roles_distinct(self):
        # Интегратор связан с 2 РАЗНЫМИ системами (роль в двух ObjectSystem)
        """Счётчик систем по ролям считает уникальные системы."""
        self.assertEqual(self._entities()["ИнтеграторБ"].systems_count, 2)

    def test_entity_type_tag_class(self):
        """CSS-класс тега соответствует типу участника."""
        self.assertEqual(self.vendor.entity_type_tag_class, "tag-blue")
        self.assertEqual(self.integ.entity_type_tag_class, "tag-ok")

    def test_can_have_products_flag(self):
        """Флаг can_have_products верен для типов участника."""
        self.assertTrue(self.vendor.can_have_products)
        self.assertFalse(self.integ.can_have_products)

    def test_industries_helpers(self):
        """Вспомогательные свойства отраслей вычисляются из продуктов вендора."""
        from apps.categories.models import Category
        from apps.entities.models import VendorProfile
        from apps.system.models import VendorProduct
        from apps.entities.usecases.entity_usecase import EntityUseCase
        cats = [Category.objects.create(category_name=n, object_level=1) for n in ("A", "B", "C", "D")]
        e = EntityUseCase().create(entity_name="XИнд", entity_type="vendor")
        vp = VendorProfile.objects.get(entity=e)
        prod = VendorProduct.objects.create(product_name="P", vendor=vp)
        prod.industries.set(cats)
        # industries отсортированы по имени: A, B, C, D
        self.assertEqual(e.industries_first, "A")
        self.assertEqual(e.industries_first_three, "A, B, C")

    def test_list_page_shows_colored_type_and_counts(self):
        """Список показывает цветной тип и счётчики."""
        h = self.client.get("/entities/").content.decode()
        self.assertIn("tag-blue", h)          # тип вендора цветной
        self.assertIn("ordering=-systems_count", h)  # колонка/сортировка счётчика систем

    def test_cards_page(self):
        """Страница карточек участников открывается."""
        h = self.client.get("/entities/cards/").content.decode()
        self.assertEqual(self.client.get("/entities/cards/").status_code, 200)
        self.assertIn("cards-grid", h)
        self.assertIn("data-href=", h)

    def test_sort_by_is_partner(self):
        """Сортировка участников по признаку партнёрства."""
        from apps.entities.usecases.entity_usecase import EntityUseCase
        # is_partner desc -> партнёр (ВендорА) первым среди этих двух
        names = [e.entity_name for e in EntityUseCase().list(ordering="-is_partner")]
        self.assertLess(names.index("ВендорА"), names.index("ИнтеграторБ"))

    def test_sort_by_systems_count(self):
        """Сортировка участников по числу систем."""
        from apps.entities.usecases.entity_usecase import EntityUseCase
        names = [e.entity_name for e in EntityUseCase().list(ordering="-systems_count")]
        # ИнтеграторБ (2) должен быть раньше ВендорА (1)
        self.assertLess(names.index("ИнтеграторБ"), names.index("ВендорА"))

    def test_detail_shows_products_block_for_vendor(self):
        """Деталь вендора показывает блок продуктов."""
        h = self.client.get(f"/entities/{self.vendor.pk}/", follow=True).content.decode()
        # У вендора блок продуктов озаглавлен «Программные продукты».
        self.assertIn("Программные продукты", h)
        self.assertIn("Продукт-1", h)

    def test_detail_no_products_block_for_integrator(self):
        """Деталь интегратора не показывает блок продуктов."""
        h = self.client.get(f"/entities/{self.integ.pk}/", follow=True).content.decode()
        self.assertNotIn("Вендорские продукты", h)


class DetailSummaryPanelTests(TestCase):
    """Сводная панель справа в детальных карточках (объект/система/участник)."""

    def setUp(self):
        """Готовит тестовые данные перед каждым тестом."""
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
            autosystem_name="СистемаП", system_class=self.cls, product=self.product, creator=self.user)
        self.obj = Object.objects.create(object_name="ОбъектП", hierarchy_level=1, creator=self.user)
        ObjectSystem.objects.create(
            object=self.obj, system=self.system, implementor=self.impl)

    def test_object_summary_panel(self):
        """Панель сводки в деталях объекта отображается корректно."""
        h = self.client.get(f"/objects/{self.obj.pk}/").content.decode()
        self.assertIn("summary-panel", h)
        self.assertIn("Сводка связанности", h)
        # агрегаты из таблицы систем: класс, вендор (через product.vendor),
        # исполнитель
        self.assertIn("SCADA", h)
        self.assertIn("Вендоры", h)
        self.assertIn("ВендорП", h)
        self.assertIn("ИсполП", h)

    def test_system_summary_panel(self):
        """Панель сводки в деталях системы отображается корректно."""
        h = self.client.get(f"/system/{self.system.pk}/").content.decode()
        self.assertIn("summary-panel", h)
        self.assertIn("Сводка связанности", h)
        self.assertIn("Исполнители", h)
        self.assertIn("ИсполП", h)

    def test_entity_summary_panel(self):
        # у исполнителя сводка показывает классы внедрённых систем
        """Панель сводки в деталях участника отображается корректно."""
        h = self.client.get(f"/entities/{self.impl.pk}/", follow=True).content.decode()
        self.assertIn("summary-panel", h)
        self.assertIn("Классы внедрённых систем", h)
        self.assertIn("SCADA", h)
        self.assertIn("Внедр. систем", h)

    def test_entity_summary_products_only_for_vendor_types(self):
        """Блок продуктов в сводке — только для вендорских типов."""
        hv = self.client.get(f"/entities/{self.vendor.pk}/", follow=True).content.decode()
        # у вендора в сводке есть метрика продуктов и классы вендорских продуктов
        self.assertIn("Продуктов", hv)
        self.assertIn("Классы вендорских продуктов", hv)
        hi = self.client.get(f"/entities/{self.impl.pk}/", follow=True).content.decode()
        # инжиниринговая компания — без продуктов и вендорских продуктов в сводке
        self.assertNotIn("Продуктов", hi)
        self.assertNotIn("Классы вендорских продуктов", hi)


class SummaryLimitTests(TestCase):
    """Сводка показывает ВСЕ элементы группы (без «ещё N») — панель прокручивается."""

    def setUp(self):
        """Готовит тестовые данные перед каждым тестом."""
        from apps.system.models import AutomationClass, AutomationSystem
        from apps.objects.models import Object, ObjectSystem
        self.user = User.objects.create_user("lim", "lim@x.x", "pw")
        self.cls = AutomationClass.objects.create(level=2, system_class="SCADA")
        self.obj = Object.objects.create(object_name="ОбъектЛ", hierarchy_level=1, creator=self.user)
        # 7 разных интеграторов -> в сводке показываются все 7, без «ещё N»
        for i in range(7):
            e = Entity.objects.create(entity_name=f"Инт{i}", entity_type="system_integrator")
            s = AutomationSystem.objects.create(
                autosystem_name=f"С{i}", system_class=self.cls, creator=self.user)
            ObjectSystem.objects.create(object=self.obj, system=s, implementor=e)

    def test_object_summary_shows_all_no_more(self):
        """Сводка показывает все элементы группы без приписки «ещё N»."""
        h = self.client.get(f"/objects/{self.obj.pk}/").content.decode()
        panel = h.split('summary-panel', 1)[1]
        # приписки «ещё N» больше нет
        self.assertNotIn("ещё ", panel)
        # показаны все 7 интеграторов
        for i in range(7):
            self.assertIn(f"Инт{i}", panel)
        # метрика систем = 7
        self.assertIn(">7<", panel)


class EntityTypingProfilesTests(TestCase):
    """Типизация Entity через профили: авто-создание/удаление и данные инж. компании."""

    def setUp(self):
        """Готовит тестовые данные перед каждым тестом."""
        from apps.system.models import AutomationClass
        from apps.objects.models import Object
        self.user = User.objects.create_user("typ", "typ@x.x", "pw")
        self.client.force_login(self.user)
        self.cls = AutomationClass.objects.create(level=3, system_class="MES")
        self.obj = Object.objects.create(object_name="ЗаводТ", hierarchy_level=1, region="Урал", creator=self.user)

    def _uc(self):
        """Возвращает экземпляр EntityUseCase (вспомогательная)."""
        from apps.entities.usecases.entity_usecase import EntityUseCase
        return EntityUseCase()

    def test_vendor_profile_autocreated_and_removed(self):
        """Профиль вендора авто-создаётся и удаляется при смене типа."""
        from apps.entities.models import VendorProfile
        e = self._uc().create(entity_name="В1", entity_type="vendor")
        self.assertTrue(VendorProfile.objects.filter(entity=e).exists())
        # смена типа на интегратора удаляет пустой профиль вендора
        self._uc().update(e.pk, entity_name="В1", entity_type="system_integrator")
        self.assertFalse(VendorProfile.objects.filter(entity=e).exists())

    def test_vendor_profile_kept_if_has_products(self):
        """Профиль вендора не удаляется, если на него ссылаются продукты."""
        from apps.entities.models import VendorProfile
        from apps.system.models import VendorProduct
        e = self._uc().create(entity_name="В2", entity_type="vendor")
        prof = VendorProfile.objects.get(entity=e)
        VendorProduct.objects.create(product_name="P", vendor=prof)
        # смена типа НЕ удаляет профиль, пока есть продукты
        self._uc().update(e.pk, entity_name="В2", entity_type="supplier")
        self.assertTrue(VendorProfile.objects.filter(entity=e).exists())

    def test_engineering_profile_autocreated(self):
        """Профиль инж. компании авто-создаётся для нужного типа."""
        from apps.entities.models import EngineeringCompanyProfile
        e = self._uc().create(entity_name="ИК", entity_type="engineering_company")
        self.assertTrue(EngineeringCompanyProfile.objects.filter(entity=e).exists())

    def test_supplier_profile_autocreated_and_removed(self):
        """Профиль поставщика авто-создаётся и удаляется при смене типа."""
        from apps.entities.models import SupplierProfile
        e = self._uc().create(entity_name="Пост1", entity_type="supplier")
        self.assertTrue(SupplierProfile.objects.filter(entity=e).exists())
        # смена типа удаляет профиль поставщика (связь неэксклюзивная)
        self._uc().update(e.pk, entity_name="Пост1", entity_type="system_integrator")
        self.assertFalse(SupplierProfile.objects.filter(entity=e).exists())

    def test_supplier_products_are_multiple_and_independent_of_vendor(self):
        """Продукты поставщика множественны и независимы от вендора."""
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
        """HTML-форма поставщика сохраняет поставляемые продукты."""
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
        """Форма участника показывает блок поставщика для нужного типа."""
        from apps.system.models import VendorProduct
        VendorProduct.objects.create(product_name="ПродДляБлока")
        h = self.client.get("/entities/create/").content.decode()
        self.assertIn('data-for="supplier full_cycle_vendor"', h)
        self.assertIn('id="supplierProductsPicker"', h)
        self.assertIn('name="supplier_products"', h)

    def test_full_cycle_vendor_has_all_three_profiles(self):
        """Вендор полного цикла = вендор + поставщик + инж. компания + dedicated профиль."""
        from apps.entities.models import (
            VendorProfile, SupplierProfile, EngineeringCompanyProfile,
            FullCycleVendorProfile,
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

    def test_full_cycle_competency_preselects_own_products(self):
        """Продукты этого вендора предвыбраны в специализации по продуктам (форма)."""
        from apps.entities.models import VendorProfile
        from apps.system.models import VendorProduct
        e = self._uc().create(entity_name="ФПЦпред", entity_type="full_cycle_vendor")
        vp = VendorProfile.objects.get(entity=e)
        own = VendorProduct.objects.create(product_name="СвойПрод", vendor=vp)
        other = VendorProduct.objects.create(product_name="ЧужойПрод")
        h = self.client.get(f"/entities/{e.pk}/edit/").content.decode()
        # свой продукт — группа "own" и отмечен selected
        self.assertIn('data-group="own"', h)
        self.assertIn("Продукты этого вендора", h)
        # предвыбор: свой продукт попал в скрытые input'ы компетенции
        self.assertIn(f'name="product_competencies" value="{own.pk}"', h)
        # чужой продукт есть в списке, но НЕ предвыбран
        self.assertNotIn(f'name="product_competencies" value="{other.pk}"', h)

    def test_full_cycle_vendor_saves_supplier_and_engineering(self):
        """ФПЦ через форму сохраняет данные поставщика и инж. компании."""
        from apps.entities.models import Entity
        from apps.system.models import VendorProduct
        from apps.categories.models import Category
        ind = Category.objects.create(category_name="Химия", object_level=1)
        prod = VendorProduct.objects.create(product_name="ФПЦпрод")
        r = self.client.post("/entities/create/", {
            "entity_name": "ФПЦФорма", "entity_type": "full_cycle_vendor",
            "supplier_products": [str(prod.pk)],
            "region": "Урал",
            "comp_class": [str(self.cls.pk)], "comp_industry": [str(ind.pk)],
        })
        self.assertEqual(r.status_code, 302)
        e = Entity.objects.get(entity_name="ФПЦФорма")
        # поставщик
        self.assertEqual(list(e.supplier_profile.products.values_list("pk", flat=True)), [prod.pk])
        # инж. компания
        self.assertEqual(e.engineering_profile.region, "Урал")
        self.assertEqual(e.engineering_profile.function_competencies.count(), 1)

    def test_system_integrator_profile_autocreated_and_removed(self):
        """Профиль интегратора авто-создаётся и удаляется при смене типа."""
        from apps.entities.models import SystemIntegratorProfile
        e = self._uc().create(entity_name="СИ1", entity_type="system_integrator")
        self.assertTrue(SystemIntegratorProfile.objects.filter(entity=e).exists())
        self._uc().update(e.pk, entity_name="СИ1", entity_type="supplier")
        self.assertFalse(SystemIntegratorProfile.objects.filter(entity=e).exists())

    def test_system_integrator_partners_and_owner(self):
        """Профиль интегратора хранит партнёров и управляющую компанию."""
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

    def test_integrator_exclusions_saved_with_nullable(self):
        """Исключения интегратора сохраняются с nullable-ссылками (пусто = «все»)."""
        from apps.entities.models import SystemIntegratorFunctionCompetency
        from apps.categories.models import Category
        cls = self.cls  # AutomationClass из setUp
        ind = Category.objects.create(category_name="ОтрасльИскл", object_level=1)
        si = self._uc().create(entity_name="ИнтегрИскл", entity_type="system_integrator")
        self._uc().save_system_integrator_profile(
            si,
            exclusions=[
                (str(cls.pk), str(ind.pk)),   # класс + отрасль
                (str(cls.pk), ""),             # класс во всех отраслях
                ("", str(ind.pk)),             # вся отрасль
                ("", ""),                       # обе пустые — отбрасывается
            ],
        )
        excl = SystemIntegratorFunctionCompetency.objects.filter(profile__entity=si)
        self.assertEqual(excl.count(), 3)  # четвёртая (обе пустые) отброшена
        # есть исключение только по классу (industry null)
        self.assertTrue(excl.filter(system_class=cls, industry__isnull=True).exists())
        # есть исключение только по отрасли (class null)
        self.assertTrue(excl.filter(system_class__isnull=True, industry=ind).exists())

    def test_engineering_competency_allows_all(self):
        """Компетенция инж. компании допускает пустой класс/отрасль (= «все»)."""
        from apps.entities.models import EngineeringCompanyFunctionCompetency
        from apps.categories.models import Category
        ind = Category.objects.create(category_name="ОтрасльВсе", object_level=1)
        e = self._uc().create(entity_name="ИКвсе", entity_type="engineering_company")
        self._uc().save_engineering_profile(
            e, region="", resident_object_id=None, product_ids=[],
            competencies=[("", str(ind.pk)), (str(self.cls.pk), "")])
        comps = EngineeringCompanyFunctionCompetency.objects.filter(profile__entity=e)
        self.assertEqual(comps.count(), 2)
        self.assertTrue(comps.filter(system_class__isnull=True, industry=ind).exists())
        self.assertTrue(comps.filter(system_class=self.cls, industry__isnull=True).exists())

    def test_web_system_integrator_saves_profile(self):
        """HTML-форма интегратора сохраняет профиль."""
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
        """Форма участника показывает блок интегратора для нужного типа."""
        from apps.owners.models import OwnerEntity
        OwnerEntity.objects.create(owner_name="Х")
        v = self._uc().create(entity_name="ВенДляБлока", entity_type="vendor")
        h = self.client.get("/entities/create/").content.decode()
        self.assertIn('data-for="system_integrator"', h)
        self.assertIn('name="managing_owner"', h)
        self.assertIn('id="vendorPartnersPicker"', h)
        self.assertIn('name="vendor_partners"', h)

    def test_product_only_for_vendor_types(self):
        """Блок продуктов доступен только для вендорских типов."""
        from django.core.exceptions import ValidationError
        from apps.system.usecases.vendor_product_usecase import VendorProductUseCase
        integ = self._uc().create(entity_name="Инт", entity_type="system_integrator")
        with self.assertRaises(ValidationError):
            VendorProductUseCase().create(product_name="X", vendor=integ.pk)

    def test_web_create_engineering_with_profile_fields(self):
        """HTML-создание инж. компании сохраняет поля профиля."""
        from apps.entities.models import Entity, VendorProfile
        from apps.system.models import VendorProduct
        from apps.categories.models import Category
        ind = Category.objects.create(category_name="Нефтехимия", object_level=1)
        vend = self._uc().create(entity_name="ВендорПрод", entity_type="vendor")
        product = VendorProduct.objects.create(product_name="Prod1", vendor=VendorProfile.objects.get(entity=vend))
        r = self.client.post("/entities/create/", {
            "entity_name": "ИнжКомп",
            "entity_type": "engineering_company",
            "region": "Урал",
            "resident_object": str(self.obj.pk),
            "product_competencies": [str(product.pk)],
            "comp_class": [str(self.cls.pk), ""],
            "comp_industry": [str(ind.pk), ""],  # id категории; вторая без класса — отброшена
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
        self.assertEqual(fc.industry_id, ind.pk)

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
        """Форма участника показывает секцию инж. компании."""
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
        """Если продуктов нет — пикер всё равно есть, показывается пояснение."""
        from apps.system.models import VendorProduct
        VendorProduct.objects.all().delete()
        h = self.client.get("/entities/create/").content.decode()
        # Поле (пикер) присутствует всегда — label без него «висел» бы пустым.
        self.assertIn('id="vendorProductsPicker"', h)
        # Пояснение для пустого списка продуктов.
        self.assertIn("Доступных продуктов нет, создайте их после вендора.", h)

    def test_detail_shows_engineering_block(self):
        """Деталь участника показывает блок инж. компании."""
        from apps.categories.models import Category
        ind = Category.objects.create(category_name="Химия", object_level=1)
        e = self._uc().create(entity_name="ИК2", entity_type="engineering_company")
        self._uc().save_engineering_profile(
            e, region="Сибирь", resident_object_id=self.obj.pk,
            product_ids=[], competencies=[(self.cls.pk, ind.pk)])
        h = self.client.get(f"/entities/{e.pk}/", follow=True).content.decode()
        self.assertIn("Инжиниринговая компания", h)
        self.assertIn("Сибирь", h)
        self.assertIn("Химия", h)


class EngineeringProfileAPITests(TestCase):
    """REST API профиля инжиниринговой компании."""

    def setUp(self):
        """Готовит тестовые данные перед каждым тестом."""
        from rest_framework.test import APIClient
        from apps.system.models import AutomationClass, VendorProduct
        from apps.objects.models import Object
        from apps.entities.models import VendorProfile
        from apps.entities.usecases.entity_usecase import EntityUseCase

        self.user = User.objects.create_user("api", "api@x.x", "pw")
        self.api = APIClient()
        from apps.categories.models import Category
        self.cls = AutomationClass.objects.create(level=3, system_class="MES")
        self.industry = Category.objects.create(category_name="Нефтехимия", object_level=1)
        self.obj = Object.objects.create(object_name="ОбъектAPI", hierarchy_level=1, creator=self.user)
        vend = EntityUseCase().create(entity_name="ВендAPI", entity_type="vendor")
        self.product = VendorProduct.objects.create(
            product_name="ProdAPI", vendor=VendorProfile.objects.get(entity=vend))
        self.eng = EntityUseCase().create(entity_name="ИнжAPI", entity_type="engineering_company")

    def test_put_and_get_engineering_profile(self):
        """PUT/GET профиля инж. компании через API."""
        self.api.force_authenticate(user=self.user)
        r = self.api.put(f"/api/entities/{self.eng.pk}/engineering-profile/", {
            "region": "Урал",
            "resident_object": self.obj.pk,
            "product_competencies": [self.product.pk],
            "function_competencies": [{"system_class": self.cls.pk, "industry": self.industry.pk}],
        }, format="json")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["region"], "Урал")
        self.assertEqual(r.data["resident_object"], self.obj.pk)
        self.assertEqual(r.data["product_competencies"], [self.product.pk])
        self.assertEqual(len(r.data["function_competencies"]), 1)
        self.assertEqual(r.data["function_competencies"][0]["industry"], self.industry.pk)
        self.assertEqual(r.data["function_competencies"][0]["industry_name"], "Нефтехимия")

        # GET доступен без авторизации
        r = self.api.get(f"/api/entities/{self.eng.pk}/engineering-profile/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["region"], "Урал")

    def test_put_rejected_for_non_engineering(self):
        """PUT профиля отклоняется для не-инж. компании."""
        from apps.entities.usecases.entity_usecase import EntityUseCase
        integ = EntityUseCase().create(entity_name="ИнтAPI", entity_type="system_integrator")
        self.api.force_authenticate(user=self.user)
        r = self.api.put(f"/api/entities/{integ.pk}/engineering-profile/",
                         {"region": "X"}, format="json")
        self.assertEqual(r.status_code, 400)

    def test_get_404_when_no_profile(self):
        """GET профиля возвращает 404 при его отсутствии."""
        from apps.entities.usecases.entity_usecase import EntityUseCase
        sup = EntityUseCase().create(entity_name="ПостAPI", entity_type="supplier")
        r = self.api.get(f"/api/entities/{sup.pk}/engineering-profile/")
        self.assertEqual(r.status_code, 404)

    def test_entity_detail_api_includes_profile(self):
        """Деталь участника в API включает профиль."""
        from apps.entities.usecases.entity_usecase import EntityUseCase
        EntityUseCase().save_engineering_profile(
            self.eng, region="Сибирь", resident_object_id=None,
            product_ids=[self.product.pk], competencies=[(self.cls.pk, self.industry.pk)])
        r = self.api.get(f"/api/entities/{self.eng.pk}/")
        self.assertEqual(r.status_code, 200)
        self.assertIsNotNone(r.data["engineering_profile"])
        self.assertEqual(r.data["engineering_profile"]["region"], "Сибирь")

    def test_put_requires_auth(self):
        """Запись профиля через API требует авторизации."""
        r = self.api.put(f"/api/entities/{self.eng.pk}/engineering-profile/",
                         {"region": "X"}, format="json")
        self.assertIn(r.status_code, (401, 403))


class EntityProfileAPICoverageTests(TestCase):
    """API-паритет с HTML: продукты вендора/поставщика, профили интегратора и ФПЦ."""

    def setUp(self):
        """Готовит тестовые данные перед каждым тестом."""
        from apps.system.models import AutomationClass, VendorProduct
        from apps.objects.models import Object
        from apps.entities.usecases.entity_usecase import EntityUseCase
        from apps.entities.models import VendorProfile
        from apps.owners.models import OwnerEntity
        from apps.categories.models import Category
        self.user = User.objects.create_user("apicov", "apicov@x.x", "pw")
        self.api = APIClient()
        self.cls = AutomationClass.objects.create(level=3, system_class="MES")
        self.industry = Category.objects.create(category_name="Химия", object_level=1)
        self.obj = Object.objects.create(object_name="ОбъектП", hierarchy_level=1, creator=self.user)
        self.owner = OwnerEntity.objects.create(owner_name="Холдинг")
        self.free_product = VendorProduct.objects.create(product_name="Свободный")
        # вендор с продуктом (будет партнёром интегратора)
        self.vend = EntityUseCase().create(entity_name="ВендП", entity_type="vendor")
        self.vendor_profile = VendorProfile.objects.get(entity=self.vend)

    # ---- vendor products ----
    def test_vendor_products_put_and_get(self):
        """PUT/GET продуктов вендора через API."""
        self.api.force_authenticate(user=self.user)
        r = self.api.put(
            f"/api/entities/{self.vend.pk}/vendor-products/",
            {"product_ids": [self.free_product.pk]}, format="json")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["product_ids"], [self.free_product.pk])
        r = self.api.get(f"/api/entities/{self.vend.pk}/vendor-products/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["product_ids"], [self.free_product.pk])

    def test_vendor_products_rejected_for_non_vendor(self):
        """Продукты вендора отклоняются для не-вендора."""
        from apps.entities.usecases.entity_usecase import EntityUseCase
        sup = EntityUseCase().create(entity_name="ПостВ", entity_type="supplier")
        self.api.force_authenticate(user=self.user)
        r = self.api.put(f"/api/entities/{sup.pk}/vendor-products/",
                         {"product_ids": []}, format="json")
        self.assertEqual(r.status_code, 400)

    def test_vendor_products_put_requires_auth(self):
        """Запись продуктов вендора требует авторизации."""
        r = self.api.put(f"/api/entities/{self.vend.pk}/vendor-products/",
                         {"product_ids": []}, format="json")
        self.assertIn(r.status_code, (401, 403))

    # ---- supplier products ----
    def test_supplier_products_put_and_get(self):
        """PUT/GET продуктов поставщика через API."""
        from apps.entities.usecases.entity_usecase import EntityUseCase
        sup = EntityUseCase().create(entity_name="ПостП", entity_type="supplier")
        self.api.force_authenticate(user=self.user)
        r = self.api.put(
            f"/api/entities/{sup.pk}/supplier-products/",
            {"product_ids": [self.free_product.pk]}, format="json")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["products"], [self.free_product.pk])
        r = self.api.get(f"/api/entities/{sup.pk}/supplier-products/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["products"], [self.free_product.pk])

    def test_supplier_products_rejected_for_non_supplier(self):
        """Продукты поставщика отклоняются для не-поставщика."""
        self.api.force_authenticate(user=self.user)
        r = self.api.put(f"/api/entities/{self.vend.pk}/supplier-products/",
                         {"product_ids": []}, format="json")
        self.assertEqual(r.status_code, 400)

    # ---- system integrator profile ----
    def test_system_integrator_profile_put_and_get(self):
        """PUT/GET профиля системного интегратора через API."""
        from apps.entities.usecases.entity_usecase import EntityUseCase
        integ = EntityUseCase().create(entity_name="ИнтП", entity_type="system_integrator")
        self.api.force_authenticate(user=self.user)
        r = self.api.put(
            f"/api/entities/{integ.pk}/system-integrator-profile/",
            {"managing_owner": self.owner.pk,
             "vendor_partner_ids": [self.vendor_profile.pk]}, format="json")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["managing_owner"], self.owner.pk)
        self.assertEqual(r.data["vendor_partners"], [self.vendor_profile.pk])
        r = self.api.get(f"/api/entities/{integ.pk}/system-integrator-profile/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["managing_owner"], self.owner.pk)

    def test_system_integrator_profile_rejected_for_non_integrator(self):
        """Профиль интегратора отклоняется для не-интегратора."""
        self.api.force_authenticate(user=self.user)
        r = self.api.put(f"/api/entities/{self.vend.pk}/system-integrator-profile/",
                         {}, format="json")
        self.assertEqual(r.status_code, 400)

    # ---- full cycle profile ----
    def test_full_cycle_profile_put_and_get(self):
        """PUT/GET профиля вендора полного цикла через API."""
        from apps.entities.usecases.entity_usecase import EntityUseCase
        fc = EntityUseCase().create(entity_name="ФПЦП", entity_type="full_cycle_vendor")
        self.api.force_authenticate(user=self.user)
        r = self.api.put(
            f"/api/entities/{fc.pk}/full-cycle-profile/",
            {"region": "Урал", "resident_object": self.obj.pk,
             "product_competencies": [self.free_product.pk],
             "function_competencies": [{"system_class": self.cls.pk, "industry": self.industry.pk}]},
            format="json")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["region"], "Урал")
        self.assertEqual(r.data["products"], [self.free_product.pk])
        self.assertEqual(len(r.data["function_competencies"]), 1)
        r = self.api.get(f"/api/entities/{fc.pk}/full-cycle-profile/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["region"], "Урал")

    def test_full_cycle_profile_rejected_for_non_full_cycle(self):
        """Профиль ФПЦ отклоняется для не-ФПЦ."""
        self.api.force_authenticate(user=self.user)
        r = self.api.put(f"/api/entities/{self.vend.pk}/full-cycle-profile/",
                         {"region": "X"}, format="json")
        self.assertEqual(r.status_code, 400)

    def test_full_cycle_profile_404_when_no_profile(self):
        """GET профиля ФПЦ возвращает 404 при его отсутствии."""
        r = self.api.get(f"/api/entities/{self.vend.pk}/full-cycle-profile/")
        self.assertEqual(r.status_code, 404)


class CompetencyTagClassFilterTests(TestCase):
    """Фильтр competency_tag_class: цвет тега компетенции «по функции».

    Правило: класс+отрасль → tag-<level>; класс без отрасли → tag-teal;
    только отрасль (класс пустой) → tag-muted.
    """

    def setUp(self):
        """Общие справочники: класс уровня 3 и отрасль."""
        from apps.categories.models import Category
        from apps.system.models import AutomationClass
        self.cls3 = AutomationClass.objects.create(level=3, system_class="MES")
        self.ind = Category.objects.create(category_name="Химия", object_level=1)

    def _filter(self):
        from apps.entities.templatetags.entity_extras import competency_tag_class
        return competency_tag_class

    def test_class_and_industry_uses_level(self):
        """Класс + отрасль → цвет по уровню автоматизации класса."""
        from apps.entities.models import (
            EngineeringCompanyProfile, EngineeringCompanyFunctionCompetency)
        e = Entity.objects.create(entity_name="ИК", entity_type="engineering_company")
        prof = EngineeringCompanyProfile.objects.create(entity=e)
        fc = EngineeringCompanyFunctionCompetency.objects.create(
            profile=prof, system_class=self.cls3, industry=self.ind)
        self.assertEqual(self._filter()(fc), "tag-3")

    def test_class_without_industry_is_teal(self):
        """Есть класс, «Все отрасли» → бирюзовый (tag-teal)."""
        from apps.entities.models import (
            EngineeringCompanyProfile, EngineeringCompanyFunctionCompetency)
        e = Entity.objects.create(entity_name="ИК2", entity_type="engineering_company")
        prof = EngineeringCompanyProfile.objects.create(entity=e)
        fc = EngineeringCompanyFunctionCompetency.objects.create(
            profile=prof, system_class=self.cls3, industry=None)
        self.assertEqual(self._filter()(fc), "tag-teal")

    def test_industry_only_is_muted(self):
        """Только отрасль («Все классы») → серый (tag-muted)."""
        from apps.entities.models import (
            EngineeringCompanyProfile, EngineeringCompanyFunctionCompetency)
        e = Entity.objects.create(entity_name="ИК3", entity_type="engineering_company")
        prof = EngineeringCompanyProfile.objects.create(entity=e)
        fc = EngineeringCompanyFunctionCompetency.objects.create(
            profile=prof, system_class=None, industry=self.ind)
        self.assertEqual(self._filter()(fc), "tag-muted")


class DetailLayoutTests(TestCase):
    """Раскладка детальной карточки: сводка, счётчик продуктов, продукты."""

    def setUp(self):
        """Вендор+поставщик (ФПЦ) с продуктами и внедрённой системой."""
        from apps.categories.models import Category
        from apps.system.models import AutomationClass, VendorProduct, AutomationSystem
        from apps.objects.models import Object, ObjectSystem
        from apps.entities.models import VendorProfile, SupplierProfile
        from apps.entities.usecases.entity_usecase import EntityUseCase
        uc = EntityUseCase()
        self.user = User.objects.create_user("dl", "dl@x.x", "pw")
        self.cls0 = AutomationClass.objects.create(level=0, system_class="КИПиА")
        # ФПЦ: и вендор, и поставщик (профили создаются usecase-ом)
        self.fcv = uc.create(entity_name="ФПЦ", entity_type="full_cycle_vendor")
        self.vprofile = VendorProfile.objects.get(entity=self.fcv)
        self.sprofile = SupplierProfile.objects.get(entity=self.fcv)
        # 2 вендорских продукта
        self.own1 = VendorProduct.objects.create(
            product_name="Свой-1", vendor=self.vprofile, system_class=self.cls0)
        self.own2 = VendorProduct.objects.create(
            product_name="Свой-2", vendor=self.vprofile, system_class=self.cls0)
        # 1 поставляемый (чужого вендора)
        other = uc.create(entity_name="Друг", entity_type="vendor")
        oprof = VendorProfile.objects.get(entity=other)
        self.supplied = VendorProduct.objects.create(
            product_name="Постав-1", vendor=oprof, system_class=self.cls0)
        self.sprofile.products.add(self.supplied)
        # внедрённая система (ФПЦ как исполнитель)
        sys = AutomationSystem.objects.create(
            autosystem_name="Сис", system_class=self.cls0,
            product=self.own1, creator=self.user)
        obj = Object.objects.create(
            object_name="Об", hierarchy_level=1, creator=self.user)
        ObjectSystem.objects.create(
            object=obj, system=sys, status="active", implementor=self.fcv)

    def test_products_count_is_vendor_plus_supplied(self):
        """Счётчик «Продуктов» = вендорские + поставляемые (2 + 1 = 3)."""
        r = self.client.get(f"/entities/{self.fcv.pk}/", follow=True)
        self.assertEqual(r.context["summary"]["products_count"], 3)

    def test_summary_has_status_and_level_coverage(self):
        """Сводка содержит статусы внедрения и покрытие по уровням."""
        h = self.client.get(f"/entities/{self.fcv.pk}/", follow=True).content.decode()
        self.assertIn("Статусы внедрения", h)
        self.assertIn("Системы по уровням", h)

    def test_supplied_products_shown_with_system_count(self):
        """Поставляемые продукты — со столбцом «Систем»."""
        h = self.client.get(f"/entities/{self.fcv.pk}/", follow=True).content.decode()
        self.assertIn("Поставляемые продукты", h)
        self.assertIn("Постав-1", h)
        self.assertIn("<th>Систем</th>", h)


class SummaryPerTypeTests(TestCase):
    """Сводка связанности: наполнение групп зависит от типа участника."""

    def setUp(self):
        """ФПЦ (вендор+поставщик), интегратор с внедрением на продукте вендора."""
        from apps.categories.models import Category
        from apps.system.models import AutomationClass, VendorProduct, AutomationSystem
        from apps.objects.models import Object, ObjectSystem
        from apps.entities.models import VendorProfile, SupplierProfile
        from apps.entities.usecases.entity_usecase import EntityUseCase
        uc = EntityUseCase()
        self.user = User.objects.create_user("spt", "spt@x.x", "pw")
        self.cls0 = AutomationClass.objects.create(level=0, system_class="КИПиА")
        self.cls2 = AutomationClass.objects.create(level=2, system_class="DCS")
        # Вендор + его продукт + система на продукте
        self.vendor = uc.create(entity_name="ВендорX", entity_type="vendor")
        vp = VendorProfile.objects.get(entity=self.vendor)
        self.prod = VendorProduct.objects.create(
            product_name="Прод-DCS", vendor=vp, system_class=self.cls2)
        self.system = AutomationSystem.objects.create(
            autosystem_name="Сис-DCS", system_class=self.cls2,
            product=self.prod, creator=self.user)
        # ФПЦ: вендор + поставщик
        self.fcv = uc.create(entity_name="ФПЦX", entity_type="full_cycle_vendor")
        fvp = VendorProfile.objects.get(entity=self.fcv)
        VendorProduct.objects.create(
            product_name="ФПЦ-own", vendor=fvp, system_class=self.cls0)
        sp = SupplierProfile.objects.get(entity=self.fcv)
        sp.products.add(self.prod)  # поставляет чужой DCS-продукт
        # Интегратор: внедрил систему на продукте ВендораX
        self.integ = uc.create(entity_name="ИнтегX", entity_type="system_integrator")
        obj = Object.objects.create(object_name="ОбъX", hierarchy_level=1, creator=self.user)
        ObjectSystem.objects.create(
            object=obj, system=self.system, status="active", implementor=self.integ)

    def test_integrator_shows_implemented_vendors(self):
        """У интегратора в сводке — вендоры установленных продуктов."""
        h = self.client.get(f"/entities/{self.integ.pk}/", follow=True).content.decode()
        self.assertIn("Вендоры установленных продуктов", h)
        self.assertIn("ВендорX", h)
        self.assertIn("Статусы внедрения", h)

    def test_vendor_shows_vendor_product_classes(self):
        """У вендора в сводке — классы вендорских продуктов, без внедрений."""
        h = self.client.get(f"/entities/{self.vendor.pk}/", follow=True).content.decode()
        self.assertIn("Классы вендорских продуктов", h)
        self.assertNotIn("Вендоры установленных продуктов", h)

    def test_fcv_shows_both_product_class_groups_in_two_cols(self):
        """У ФПЦ вендорские и поставляемые классы — рядом в две колонки."""
        h = self.client.get(f"/entities/{self.fcv.pk}/", follow=True).content.decode()
        self.assertIn("Классы вендорских продуктов", h)
        self.assertIn("Классы поставляемых продуктов", h)
        self.assertIn("summary-cols", h)

    def test_engineering_no_product_groups(self):
        """У инж.компании нет продуктовых групп и вендоров установленных."""
        from apps.entities.usecases.entity_usecase import EntityUseCase
        eng = EntityUseCase().create(entity_name="ИКX", entity_type="engineering_company")
        h = self.client.get(f"/entities/{eng.pk}/", follow=True).content.decode()
        self.assertNotIn("Классы вендорских продуктов", h)
        self.assertNotIn("Классы поставляемых продуктов", h)
        self.assertNotIn("Вендоры установленных продуктов", h)


class IndustriesDisplayTests(TestCase):
    """industries_display: у интегратора «Все отрасли, кроме: …»."""

    def setUp(self):
        from apps.categories.models import Category
        from apps.system.models import AutomationClass
        self.cls = AutomationClass.objects.create(level=3, system_class="MES")
        self.ind = Category.objects.create(category_name="Фарма", object_level=1)

    def _uc(self):
        from apps.entities.usecases.entity_usecase import EntityUseCase
        return EntityUseCase()

    def test_integrator_all_except_excluded_industries(self):
        """Исключение с отраслью → «Все отрасли, кроме: <отрасль>»."""
        e = self._uc().create(entity_name="Инт1", entity_type="system_integrator")
        self._uc().save_system_integrator_profile(
            e, managing_owner_id=None, vendor_partner_ids=[],
            exclusions=[(self.cls.pk, self.ind.pk)])
        self.assertEqual(e.industries_display, "Все отрасли, кроме: Фарма")

    def test_integrator_class_only_exclusion_is_all(self):
        """Исключение только по классу (без отрасли) → «Все отрасли»."""
        e = self._uc().create(entity_name="Инт2", entity_type="system_integrator")
        self._uc().save_system_integrator_profile(
            e, managing_owner_id=None, vendor_partner_ids=[],
            exclusions=[(self.cls.pk, "")])
        self.assertEqual(e.industries_display, "Все отрасли")

    def test_integrator_no_exclusions_is_all(self):
        """Нет исключений → «Все отрасли»."""
        e = self._uc().create(entity_name="Инт3", entity_type="system_integrator")
        self._uc().save_system_integrator_profile(
            e, managing_owner_id=None, vendor_partner_ids=[], exclusions=[])
        self.assertEqual(e.industries_display, "Все отрасли")

    def test_non_integrator_uses_industries_list(self):
        """У не-интегратора без отраслей — «—»."""
        e = self._uc().create(entity_name="Вен1", entity_type="vendor")
        self.assertEqual(e.industries_display, "—")


class EntityTypePagesRoutingTests(TestCase):
    """Раздельные страницы участника по типу + диспетчер entity-detail."""

    def setUp(self):
        from apps.entities.usecases.entity_usecase import EntityUseCase
        uc = EntityUseCase()
        self.by_type = {
            t: uc.create(entity_name=f"Комп-{t}", entity_type=t)
            for t in ["vendor", "supplier", "system_integrator",
                      "engineering_company", "full_cycle_vendor"]
        }

    def test_dispatcher_redirects_to_type_page(self):
        """entity/<id>/ редиректит на типовую страницу по типу участника."""
        for t, e in self.by_type.items():
            r = self.client.get(f"/entities/{e.pk}/")
            self.assertEqual(r.status_code, 302)
            self.assertEqual(r.headers["Location"], f"/entities/{e.pk}/{t}/")

    def test_type_pages_render(self):
        """Каждая типовая страница отдаётся со статусом 200."""
        for t, e in self.by_type.items():
            r = self.client.get(f"/entities/{e.pk}/{t}/")
            self.assertEqual(r.status_code, 200)
            self.assertContains(r, e.entity_name)

    def test_wrong_type_url_redirects_to_correct(self):
        """URL с неверным типом редиректит на правильную страницу участника."""
        vendor = self.by_type["vendor"]
        r = self.client.get(f"/entities/{vendor.pk}/supplier/")
        self.assertEqual(r.status_code, 302)
        self.assertEqual(r.headers["Location"], f"/entities/{vendor.pk}/vendor/")

    def test_typeless_entity_falls_back_to_list(self):
        """Участник без типа: диспетчер ведёт на список (нет своей страницы)."""
        e = Entity.objects.create(entity_name="БезТипа")
        r = self.client.get(f"/entities/{e.pk}/")
        self.assertEqual(r.status_code, 302)
        self.assertEqual(r.headers["Location"], "/entities/")


class MiniCardCountersTests(TestCase):
    """Счётчики мини-карточки согласованы со сводкой (продукты и системы)."""

    def setUp(self):
        from apps.system.models import AutomationClass, VendorProduct, AutomationSystem
        from apps.objects.models import Object, ObjectSystem
        from apps.entities.models import VendorProfile, SupplierProfile
        from apps.entities.usecases.entity_usecase import EntityUseCase
        from apps.entities.repositories.entity_repository import EntityRepository
        self.repo = EntityRepository()
        self.user = User.objects.create_user("mc", "mc@x.x", "pw")
        self.cls = AutomationClass.objects.create(level=2, system_class="DCS")
        uc = EntityUseCase()
        # Вендор с продуктом
        self.vendor = uc.create(entity_name="ВендорМК", entity_type="vendor")
        vp = VendorProfile.objects.get(entity=self.vendor)
        self.prod = VendorProduct.objects.create(
            product_name="ПродуктМК", vendor=vp, system_class=self.cls)
        # Система на продукте (вендорская система)
        self.system = AutomationSystem.objects.create(
            autosystem_name="СисМК", system_class=self.cls,
            product=self.prod, creator=self.user)
        # Поставщик, поставляет чужой продукт
        self.supplier = uc.create(entity_name="ПоставщикМК", entity_type="supplier")
        uc.save_supplier_products(self.supplier, product_ids=[self.prod.pk])
        # Интегратор, внедрил одну систему на ДВУХ объектах (2 связи, 1 система)
        self.integ = uc.create(entity_name="ИнтегМК", entity_type="system_integrator")
        for i in range(2):
            o = Object.objects.create(
                object_name=f"ОбъМК{i}", hierarchy_level=1, creator=self.user)
            ObjectSystem.objects.create(
                object=o, system=self.system, implementor=self.integ)

    def test_supplier_products_count_uses_supplied(self):
        """У поставщика products_count = число поставляемых продуктов (не 0)."""
        a = self.repo.get_by_id(self.supplier.pk)
        self.assertEqual(a.products_count, 1)

    def test_vendor_products_count_uses_vendor(self):
        """У вендора products_count = число его вендорских продуктов."""
        a = self.repo.get_by_id(self.vendor.pk)
        self.assertEqual(a.products_count, 1)

    def test_integrator_systems_count_counts_links_not_distinct(self):
        """У интегратора systems_count = число внедрений (связей), а не систем.

        Одна система на 2 объектах — это 2 внедрения (совпадает со сводкой).
        """
        a = self.repo.get_by_id(self.integ.pk)
        self.assertEqual(a.systems_count, 2)

    def test_vendor_systems_count_counts_product_systems(self):
        """У вендора systems_count = число вендорских систем (на его продуктах)."""
        a = self.repo.get_by_id(self.vendor.pk)
        self.assertEqual(a.systems_count, 1)


class SupplierSystemsCountTests(TestCase):
    """Счётчик систем поставщика — по поставленным связям (не внедрённым)."""

    def setUp(self):
        from apps.system.models import AutomationClass, VendorProduct, AutomationSystem
        from apps.objects.models import Object, ObjectSystem
        from apps.entities.usecases.entity_usecase import EntityUseCase
        from apps.entities.repositories.entity_repository import EntityRepository
        self.repo = EntityRepository()
        self.user = User.objects.create_user("ssc", "ssc@x.x", "pw")
        uc = EntityUseCase()
        self.supplier = uc.create(entity_name="ПоставщикСч", entity_type="supplier")
        cls = AutomationClass.objects.create(level=2, system_class="DCS")
        prod = VendorProduct.objects.create(product_name="ПрСч", system_class=cls)
        sysm = AutomationSystem.objects.create(
            autosystem_name="СисСч", system_class=cls, product=prod, creator=self.user)
        # 2 объекта, где этот поставщик — поставщик системы
        for i in range(2):
            o = Object.objects.create(
                object_name=f"ОбСч{i}", hierarchy_level=1, creator=self.user)
            ObjectSystem.objects.create(object=o, system=sysm, supplier=self.supplier)

    def test_mini_card_counts_supplied(self):
        """Мини-карточка: systems_count = число поставленных связей."""
        a = self.repo.get_by_id(self.supplier.pk)
        self.assertEqual(a.systems_count, 2)

    def test_summary_shows_supplied_count(self):
        """Сводка поставщика: метрика «Поставлено систем» = 2."""
        h = self.client.get(f"/entities/{self.supplier.pk}/supplier/").content.decode()
        self.assertIn("Поставлено систем", h)
        self.assertNotIn("Внедр. систем", h)
        import re
        m = dict((lbl, int(n)) for n, lbl in re.findall(
            r'metric-num">(\d+)</span><span class="metric-label">([^<]+)</span>', h))
        self.assertEqual(m.get("Поставлено систем"), 2)
