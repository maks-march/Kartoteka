"""Серверная сортировка и паритет фильтров системного API.

Принцип: фильтрация и сортировка выполняются на бэкенде (ORDER BY / WHERE),
у них есть протестированные эндпоинты, а не клиентский JS.
"""
from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from apps.system.models import AutomationClass, AutomationSystem, VendorProduct
from apps.system.usecases.system_usecase import SystemUseCase


class SystemOrderingTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("o", "o@o.o", "pw")
        self.cls = AutomationClass.objects.create(level=2, system_class="SCADA", description="")
        self.pb = VendorProduct.objects.create(product_name="Бета-продукт")
        self.pa = VendorProduct.objects.create(product_name="Альфа-продукт")
        self.pg = VendorProduct.objects.create(product_name="Гамма-продукт")
        AutomationSystem.objects.create(autosystem_name="Бета", system_class=self.cls, product=self.pb, creator_id=self.user)
        AutomationSystem.objects.create(autosystem_name="Альфа", system_class=self.cls, product=self.pa, creator_id=self.user)
        AutomationSystem.objects.create(autosystem_name="Гамма", system_class=self.cls, product=self.pg, creator_id=self.user)

    def _names(self, ordering):
        return [s.autosystem_name for s in SystemUseCase().list(ordering=ordering)]

    def test_default_ordering_by_name(self):
        self.assertEqual(self._names(None), ["Альфа", "Бета", "Гамма"])

    def test_ordering_desc_by_name(self):
        self.assertEqual(self._names("-autosystem_name"), ["Гамма", "Бета", "Альфа"])

    def test_ordering_by_product_name(self):
        # Альфа-продукт < Бета-продукт < Гамма-продукт
        self.assertEqual(self._names("product__product_name"), ["Альфа", "Бета", "Гамма"])

    def test_invalid_ordering_field_falls_back_to_default(self):
        # Защита от инъекции произвольного поля: берётся сортировка по умолчанию.
        self.assertEqual(self._names("creator_id__password"), ["Альфа", "Бета", "Гамма"])

    def test_api_ordering(self):
        c = APIClient()
        resp = c.get("/api/system/", {"ordering": "-autosystem_name"})
        self.assertEqual(resp.status_code, 200)
        names = [row["autosystem_name"] for row in resp.data]
        self.assertEqual(names, ["Гамма", "Бета", "Альфа"])


class SystemApiFilterParityTests(TestCase):
    """Новые критерии фильтрации должны работать и через REST API."""

    def setUp(self):
        self.user = User.objects.create_user("p", "p@p.p", "pw")
        self.cls = AutomationClass.objects.create(level=2, system_class="SCADA", description="")
        self.p1 = VendorProduct.objects.create(product_name="Simatic")
        self.p2 = VendorProduct.objects.create(product_name="Experion")
        self.s1 = AutomationSystem.objects.create(
            autosystem_name="S1", system_class=self.cls, product=self.p1,
            system_status="active", creator_id=self.user,
        )
        self.s2 = AutomationSystem.objects.create(
            autosystem_name="S2", system_class=self.cls, product=self.p2,
            system_status="planned", creator_id=self.user,
        )
        self.client_api = APIClient()

    def _names(self, params):
        resp = self.client_api.get("/api/system/", params)
        self.assertEqual(resp.status_code, 200)
        return sorted(row["autosystem_name"] for row in resp.data)

    def test_api_filter_by_product(self):
        self.assertEqual(self._names({"product": self.p1.pk}), ["S1"])

    def test_api_filter_by_status(self):
        self.assertEqual(self._names({"system_status": "planned"}), ["S2"])

    def test_api_filters_combine_with_and(self):
        self.assertEqual(self._names({"product": self.p1.pk, "system_status": "active"}), ["S1"])
        self.assertEqual(self._names({"product": self.p1.pk, "system_status": "planned"}), [])

    def test_api_multiselect_product_is_or(self):
        resp = self.client_api.get(f"/api/system/?product={self.p1.pk}&product={self.p2.pk}")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(sorted(r["autosystem_name"] for r in resp.data), ["S1", "S2"])
