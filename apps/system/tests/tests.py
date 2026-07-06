from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from apps.categories.models import Category
from apps.objects.models import Object, ObjectSystem
from apps.system.models import AutomatedSystem, AutomationClass


class SystemEndpointTestMixin:
    def create_base_data(self):
        self.user = User.objects.create_user(username="user", password="password")
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
        self.category = Category.objects.create(name="Площадка", level=1, creator_id=self.user)
        self.object = Object.objects.create(
            name="Завод",
            level=1,
            category=self.category,
            creator_id=self.user,
        )


class SystemWebEndpointTests(SystemEndpointTestMixin, TestCase):
    def setUp(self):
        self.create_base_data()

    def test_system_list_page_is_available(self):
        response = self.client.get("/system/")
        self.assertEqual(response.status_code, 200)

    def test_system_list_supports_filters(self):
        response = self.client.get("/system/", {
            "system_class": str(self.automation_class.pk),
            "search": "асу",
        })
        self.assertEqual(response.status_code, 200)

    def test_system_detail_page_is_available(self):
        response = self.client.get(f"/system/{self.system.pk}/")
        self.assertEqual(response.status_code, 200)

    def test_system_create_page_requires_authentication(self):
        response = self.client.get("/system/create/")
        self.assertEqual(response.status_code, 302)

    def test_authenticated_system_crud_and_attach_object_endpoints(self):
        self.client.force_login(self.user)

        response = self.client.get("/system/create/")
        self.assertEqual(response.status_code, 200)

        response = self.client.post("/system/create/", {
            "autosystem_name": "MES",
            "system_class": str(self.automation_class.pk),
        })
        self.assertEqual(response.status_code, 302)
        created = AutomatedSystem.objects.get(autosystem_name="MES")

        response = self.client.get(f"/system/{created.pk}/edit/")
        self.assertEqual(response.status_code, 200)

        response = self.client.post(f"/system/{created.pk}/edit/", {
            "autosystem_name": "MES 2",
            "system_class": str(self.automation_class.pk),
        })
        self.assertEqual(response.status_code, 302)
        created.refresh_from_db()
        self.assertEqual(created.autosystem_name, "MES 2")

        response = self.client.get(f"/system/{created.pk}/attach-object/")
        self.assertEqual(response.status_code, 200)

        response = self.client.post(f"/system/{created.pk}/attach-object/", {
            "object": str(self.object.pk),
            "status": "active",
            "implementation_date": "2026-01-01",
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(ObjectSystem.objects.filter(object=self.object, system=created).exists())

        response = self.client.post(f"/system/{created.pk}/delete/")
        self.assertEqual(response.status_code, 302)
        self.assertFalse(AutomatedSystem.objects.filter(pk=created.pk).exists())


class SystemApiEndpointTests(SystemEndpointTestMixin, TestCase):
    def setUp(self):
        self.create_base_data()
        self.api_client = APIClient()

    def test_system_api_list_detail_and_classes_are_public(self):
        response = self.api_client.get("/api/system/classes/")
        self.assertEqual(response.status_code, 200)

        response = self.api_client.get("/api/system/", {
            "system_class": str(self.automation_class.pk),
            "search": "асу",
        })
        self.assertEqual(response.status_code, 200)

        response = self.api_client.get(f"/api/system/{self.system.pk}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], self.system.pk)

    def test_system_api_create_requires_authentication(self):
        response = self.api_client.post("/api/system/", {
            "autosystem_name": "API MES",
            "system_class": self.automation_class.pk,
        }, format="json")
        self.assertIn(response.status_code, (401, 403))

    def test_authenticated_system_api_crud(self):
        self.api_client.force_authenticate(user=self.user)

        response = self.api_client.post("/api/system/", {
            "autosystem_name": "API MES",
            "system_class": self.automation_class.pk,
        }, format="json")
        self.assertEqual(response.status_code, 201)
        system_id = response.data["id"]

        response = self.api_client.patch(f"/api/system/{system_id}/", {
            "autosystem_name": "API MES 2",
            "system_class": self.automation_class.pk,
        }, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["autosystem_name"], "API MES 2")

        response = self.api_client.delete(f"/api/system/{system_id}/")
        self.assertEqual(response.status_code, 204)
        self.assertFalse(AutomatedSystem.objects.filter(pk=system_id).exists())

    def test_system_api_attach_object_requires_authentication(self):
        response = self.api_client.post(
            f"/api/system/{self.system.pk}/attach-object/",
            {"object": self.object.pk},
            format="json",
        )
        self.assertIn(response.status_code, (401, 403))

    def test_authenticated_system_api_attach_object(self):
        self.api_client.force_authenticate(user=self.user)
        response = self.api_client.post(
            f"/api/system/{self.system.pk}/attach-object/",
            {
                "object": self.object.pk,
                "status": "active",
                "implementation_date": "2026-01-01",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["object"], self.object.pk)
        self.assertEqual(response.data["system"], self.system.pk)
        self.assertEqual(response.data["status"], "active")
        self.assertTrue(
            ObjectSystem.objects.filter(object=self.object, system=self.system).exists()
        )

    def test_system_api_attach_object_duplicate_is_rejected(self):
        self.api_client.force_authenticate(user=self.user)
        ObjectSystem.objects.create(object=self.object, system=self.system, status="planned")
        response = self.api_client.post(
            f"/api/system/{self.system.pk}/attach-object/",
            {"object": self.object.pk},
            format="json",
        )
        self.assertIn(response.status_code, (400, 422))

    def test_system_api_attach_object_unknown_system_returns_404(self):
        self.api_client.force_authenticate(user=self.user)
        response = self.api_client.post(
            "/api/system/999999/attach-object/",
            {"object": self.object.pk},
            format="json",
        )
        self.assertEqual(response.status_code, 404)


class SystemNewFieldsTests(SystemEndpointTestMixin, TestCase):
    """Новые поля системы: идентификация, состояние, жизненный цикл, JSON-данные."""

    def setUp(self):
        self.create_base_data()
        self.api_client = APIClient()

    # ---------- usecase / web ----------
    def test_web_create_persists_new_fields(self):
        from apps.system.models import VendorProduct
        product = VendorProduct.objects.create(product_name="PCS 7")
        self.client.force_login(self.user)
        response = self.client.post("/system/create/", {
            "autosystem_name": "PCS 7 Full",
            "autosystem_short_name": "PCS7",
            "system_class": str(self.automation_class.pk),
            "product": str(product.pk),
            "system_status": "planned",
            "notes": "Примечание",
            "release_year": "2021-05-20",
            # Технические характеристики — пары ключ/значение
            "spec_key": ["cpu", ""],
            "spec_value": ["x86", "пустой ключ игнорируется"],
            # Списки — через запятую / точку с запятой
            "modules": "m1, m2; m3",
            "interfaces": "",
        })
        self.assertEqual(response.status_code, 302)
        s = AutomatedSystem.objects.get(autosystem_name="PCS 7 Full")
        self.assertEqual(s.autosystem_short_name, "PCS7")
        self.assertEqual(s.product_id, product.pk)
        self.assertEqual(s.system_status, "planned")
        self.assertEqual(s.technical_specs, {"cpu": "x86"})
        self.assertEqual(s.modules, ["m1", "m2", "m3"])
        self.assertIsNone(s.interfaces)

    def test_status_defaults_to_active(self):
        from apps.system.usecases.system_usecase import SystemUseCase
        s = SystemUseCase().create(
            user=self.user,
            autosystem_name="Default",
            system_class=self.automation_class.pk,
        )
        self.assertEqual(s.system_status, "active")
        self.assertEqual(s.status_tag_class, "tag-ok")

    def test_create_without_product_stores_null(self):
        from apps.system.usecases.system_usecase import SystemUseCase
        uc = SystemUseCase()
        a = uc.create(user=self.user, autosystem_name="A", system_class=self.automation_class.pk)
        b = uc.create(user=self.user, autosystem_name="B", system_class=self.automation_class.pk, product=None)
        self.assertIsNone(a.product)
        self.assertIsNone(b.product)

    def test_web_create_lists_support_comma_and_semicolon(self):
        self.client.force_login(self.user)
        response = self.client.post("/system/create/", {
            "autosystem_name": "ListSep",
            "system_class": str(self.automation_class.pk),
            "modules": "A , B; C",
            "interfaces": "OPC UA; Modbus",
        })
        self.assertEqual(response.status_code, 302)
        s = AutomatedSystem.objects.get(autosystem_name="ListSep")
        self.assertEqual(s.modules, ["A", "B", "C"])
        self.assertEqual(s.interfaces, ["OPC UA", "Modbus"])

    def test_web_create_empty_lists_and_specs_stored_as_null(self):
        self.client.force_login(self.user)
        response = self.client.post("/system/create/", {
            "autosystem_name": "Empties",
            "system_class": str(self.automation_class.pk),
            "modules": "",
            "interfaces": "",
        })
        self.assertEqual(response.status_code, 302)
        s = AutomatedSystem.objects.get(autosystem_name="Empties")
        self.assertIsNone(s.modules)
        self.assertIsNone(s.interfaces)
        self.assertIsNone(s.technical_specs)

    def test_status_tag_class_mapping(self):
        s = AutomatedSystem(autosystem_name="x", system_class=self.automation_class, system_status="unsupported")
        self.assertEqual(s.status_tag_class, "tag-danger")

    # ---------- API ----------
    def test_api_create_with_new_fields(self):
        from apps.system.models import VendorProduct
        product = VendorProduct.objects.create(product_name="API Product")
        self.api_client.force_authenticate(user=self.user)
        response = self.api_client.post("/api/system/", {
            "autosystem_name": "API Sys",
            "autosystem_short_name": "AS",
            "system_class": self.automation_class.pk,
            "product": product.pk,
            "system_status": "planned",
            "technical_specs": {"ram": "16GB"},
            "modules": ["x"],
        }, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["autosystem_short_name"], "AS")
        self.assertEqual(response.data["product"], product.pk)
        self.assertEqual(response.data["product_name"], "API Product")
        self.assertEqual(response.data["system_status"], "planned")
        self.assertEqual(response.data["technical_specs"], {"ram": "16GB"})
        self.assertEqual(response.data["modules"], ["x"])

    def test_api_detail_exposes_new_fields(self):
        from apps.system.models import VendorProduct
        product = VendorProduct.objects.create(product_name="Detail Product")
        s = AutomatedSystem.objects.create(
            autosystem_name="Detail Sys",
            system_class=self.automation_class,
            product=product,
            system_status="active",
            interfaces=["OPC UA"],
            creator_id=self.user,
        )
        response = self.api_client.get(f"/api/system/{s.pk}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["product_name"], "Detail Product")
        self.assertEqual(response.data["interfaces"], ["OPC UA"])
        self.assertEqual(response.data["status_display"], "В эксплуатации")


class SystemApiPartialUpdateTests(SystemEndpointTestMixin, TestCase):
    """Регресс: частичный PATCH без system_class не должен ломать связь с классом."""

    def setUp(self):
        self.create_base_data()
        self.api_client = APIClient()

    def test_partial_patch_without_class_preserves_class_and_other_fields(self):
        self.api_client.force_authenticate(user=self.user)
        create = self.api_client.post("/api/system/", {
            "autosystem_name": "Partial",
            "system_class": self.automation_class.pk,
            "technical_specs": {"cpu": "x86"},
            "modules": ["M1", "M2"],
        }, format="json")
        self.assertEqual(create.status_code, 201)
        sid = create.data["id"]

        resp = self.api_client.patch(f"/api/system/{sid}/", {"modules": ["only"]}, format="json")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["modules"], ["only"])
        # класс и характеристики не потеряны
        self.assertEqual(resp.data["system_class"], self.automation_class.pk)
        self.assertEqual(resp.data["technical_specs"], {"cpu": "x86"})

    def test_patch_invalid_class_returns_validation_error(self):
        self.api_client.force_authenticate(user=self.user)
        create = self.api_client.post("/api/system/", {
            "autosystem_name": "P2", "system_class": self.automation_class.pk,
        }, format="json")
        sid = create.data["id"]
        resp = self.api_client.patch(f"/api/system/{sid}/", {"system_class": 999999}, format="json")
        self.assertIn(resp.status_code, (400, 422))


class SystemListFilterTests(TestCase):
    """Дополнительные критерии поиска систем: продукт, статус."""

    def setUp(self):
        from apps.system.models import VendorProduct
        self.user = User.objects.create_user(username="flt", password="pw")
        self.cls = AutomationClass.objects.create(level=2, system_class="SCADA", description="")
        self.p1 = VendorProduct.objects.create(product_name="Simatic")
        self.p2 = VendorProduct.objects.create(product_name="Experion")
        self.s1 = AutomatedSystem.objects.create(
            autosystem_name="S1", system_class=self.cls, product=self.p1,
            system_status="active", creator_id=self.user,
        )
        self.s2 = AutomatedSystem.objects.create(
            autosystem_name="S2", system_class=self.cls, product=self.p2,
            system_status="planned", creator_id=self.user,
        )

    def _names(self, params):
        from apps.system.usecases.system_usecase import SystemUseCase
        return sorted(s.autosystem_name for s in SystemUseCase().list(**params))

    def test_filter_by_product(self):
        self.assertEqual(self._names({"product": [self.p1.pk]}), ["S1"])

    def test_filter_by_status(self):
        self.assertEqual(self._names({"system_status": ["planned"]}), ["S2"])

    def test_filters_combine_with_and(self):
        self.assertEqual(self._names({"product": [self.p1.pk], "system_status": ["active"]}), ["S1"])
        self.assertEqual(self._names({"product": [self.p1.pk], "system_status": ["planned"]}), [])

    def test_multiselect_product_is_or(self):
        self.assertEqual(self._names({"product": [self.p1.pk, self.p2.pk]}), ["S1", "S2"])

    def test_web_list_renders_new_filters(self):
        from django.test import Client
        c = Client()
        h = c.get("/system/").content.decode()
        self.assertIn("Продукт", h)
        self.assertIn("Статус системы", h)

    def test_web_list_filter_by_product_narrows_rows(self):
        from django.test import Client
        c = Client()
        h = c.get("/system/", {"product": str(self.p1.pk)}).content.decode()
        self.assertIn("S1", h)
        self.assertNotIn(">S2<", h)


class SubsystemClassesTests(TestCase):
    """Классы подсистем: составные классы, авто-MES (MOM⇒MES), фильтрация,
    очистка при смене класса, отображение label (ENG (РУС))."""

    def setUp(self):
        self.user = User.objects.create_user("sub", "s@s.s", "pw")
        # Классы: MOM (составной, includes=MES), MES (составной), WMS, SCADA,
        # АСУТП (составной), обычный ERP.
        self.mes = AutomationClass.objects.create(level=3, system_class="MES", is_composite=True)
        self.mom = AutomationClass.objects.create(
            level=3, system_class="MOM", is_composite=True, includes=self.mes)
        self.wms = AutomationClass.objects.create(level=3, system_class="WMS")
        self.asutp = AutomationClass.objects.create(
            level=2, system_class="АСУТП", name_ru="", is_composite=True)
        self.dcs = AutomationClass.objects.create(level=2, system_class="DCS", name_ru="РСУ")
        self.erp = AutomationClass.objects.create(level=4, system_class="ERP")

    def _uc(self):
        from apps.system.usecases.system_usecase import SystemUseCase
        return SystemUseCase()

    def test_label_eng_and_ru(self):
        self.assertEqual(self.dcs.label, "DCS (РСУ)")
        self.assertEqual(self.mes.label, "MES")

    def test_create_composite_auto_adds_includes(self):
        # MOM без явных подсистем -> автоматически появляется MES
        s = self._uc().create(user=self.user, autosystem_name="MOM-1",
                              system_class=self.mom.pk, subsystem_classes=[])
        subs = set(s.subsystem_classes.values_list("system_class", flat=True))
        self.assertIn("MES", subs)

    def test_create_composite_keeps_selected_and_adds_includes(self):
        s = self._uc().create(user=self.user, autosystem_name="MOM-2",
                              system_class=self.mom.pk, subsystem_classes=[self.wms.pk])
        subs = set(s.subsystem_classes.values_list("system_class", flat=True))
        self.assertEqual(subs, {"WMS", "MES"})

    def test_non_composite_class_clears_subsystems(self):
        # обычный класс (WMS) -> подсистемы игнорируются
        s = self._uc().create(user=self.user, autosystem_name="Wms-only",
                              system_class=self.wms.pk, subsystem_classes=[self.mes.pk])
        self.assertEqual(s.subsystem_classes.count(), 0)

    def test_change_to_non_composite_clears_on_update(self):
        s = self._uc().create(user=self.user, autosystem_name="X",
                              system_class=self.mom.pk, subsystem_classes=[self.wms.pk])
        self.assertTrue(s.subsystem_classes.exists())
        # меняем класс на обычный -> подсистемы должны очиститься
        s = self._uc().update(pk=s.pk, user=self.user, autosystem_name="X",
                             system_class=self.wms.pk)
        self.assertEqual(s.subsystem_classes.count(), 0)

    def test_filter_by_composite_matches_subsystem(self):
        # система MES с подсистемой WMS
        self._uc().create(user=self.user, autosystem_name="MES-sys",
                         system_class=self.mes.pk, subsystem_classes=[self.wms.pk])
        # отдельная WMS-система
        self._uc().create(user=self.user, autosystem_name="WMS-sys", system_class=self.wms.pk)
        names = sorted(s.autosystem_name for s in self._uc().list(system_class=self.mes.pk))
        self.assertEqual(names, ["MES-sys"])

    def test_filter_by_ordinary_class_also_matches_subsystem(self):
        # B-б: фильтр по WMS находит и отдельную WMS, и MES где WMS в подсистемах
        self._uc().create(user=self.user, autosystem_name="MES-sys",
                         system_class=self.mes.pk, subsystem_classes=[self.wms.pk])
        self._uc().create(user=self.user, autosystem_name="WMS-sys", system_class=self.wms.pk)
        names = sorted(s.autosystem_name for s in self._uc().list(system_class=self.wms.pk))
        self.assertEqual(names, ["MES-sys", "WMS-sys"])

    def test_filter_no_duplicates(self):
        # система, где класс совпадает и как основной, и (случайно) в подсистемах
        s = self._uc().create(user=self.user, autosystem_name="MES-dup",
                             system_class=self.mes.pk, subsystem_classes=[self.wms.pk])
        # добавим сам MES в подсистемы вручную не даём (self скрыт), проверяем что
        # фильтр по MES не задваивает строку
        results = list(self._uc().list(system_class=self.mes.pk))
        self.assertEqual(len([x for x in results if x.pk == s.pk]), 1)

    def test_form_shows_subsystem_block(self):
        from django.test import Client
        c = Client(); c.force_login(self.user)
        h = c.get("/system/create/").content.decode()
        self.assertIn("subsystemsBlock", h)
        self.assertIn("Классы подсистем", h)
        # data-composite проставлен у составных классов
        self.assertIn('data-composite="1"', h)


class ClassLabelDisplayTests(TestCase):
    """Русская аббревиатура показывается только в подробной карточке (под классом),
    а в списках/тегах — только англ. код без скобок."""

    def setUp(self):
        self.user = User.objects.create_user("lbl", "l@l.l", "pw")
        self.cls = AutomationClass.objects.create(
            level=2, system_class="DCS", name_ru="РСУ",
            description="Распределённая система управления")
        from apps.system.usecases.system_usecase import SystemUseCase
        self.sys = SystemUseCase().create(
            user=self.user, autosystem_name="DCS-система", system_class=self.cls.pk)

    def test_detail_shows_ru_and_description_under_class(self):
        h = self.client.get(f"/system/{self.sys.pk}/").content.decode()
        self.assertIn("class-subinfo", h)
        self.assertIn("РСУ", h)
        self.assertIn("Распределённая система управления", h)
        # код класса тоже есть
        self.assertIn("DCS", h)
        # но не в формате «DCS (РСУ)» в теге/значении
        self.assertNotIn("DCS (РСУ)", h)

    def test_list_shows_code_only(self):
        h = self.client.get("/system/").content.decode()
        self.assertIn("DCS", h)
        self.assertNotIn("DCS (РСУ)", h)
        self.assertNotIn("class-subinfo", h)

    def test_cards_show_code_only(self):
        h = self.client.get("/system/cards/").content.decode()
        self.assertIn("DCS", h)
        self.assertNotIn("DCS (РСУ)", h)
