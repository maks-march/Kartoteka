"""Серверная сортировка и паритет фильтров системного API.

Принцип: фильтрация и сортировка выполняются на бэкенде (ORDER BY / WHERE),
у них есть протестированные эндпоинты, а не клиентский JS.
"""
from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from apps.participants.models import Participant
from apps.system.models import AutomationClass, AutomatedSystem
from apps.system.usecases.system_usecase import SystemUseCase


class SystemOrderingTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("o", "o@o.o", "pw")
        self.cls = AutomationClass.objects.create(level=2, system_class="SCADA", description="")
        AutomatedSystem.objects.create(autosystem_name="Бета", system_class=self.cls, version="2", creator_id=self.user)
        AutomatedSystem.objects.create(autosystem_name="Альфа", system_class=self.cls, version="3", creator_id=self.user)
        AutomatedSystem.objects.create(autosystem_name="Гамма", system_class=self.cls, version="1", creator_id=self.user)

    def _names(self, ordering):
        return [s.autosystem_name for s in SystemUseCase().list(ordering=ordering)]

    def test_default_ordering_by_name(self):
        self.assertEqual(self._names(None), ["Альфа", "Бета", "Гамма"])

    def test_ordering_desc_by_name(self):
        self.assertEqual(self._names("-autosystem_name"), ["Гамма", "Бета", "Альфа"])

    def test_ordering_by_version(self):
        self.assertEqual(self._names("version"), ["Гамма", "Бета", "Альфа"])

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
        self.v1 = Participant.objects.create(participant_name="Siemens")
        self.v2 = Participant.objects.create(participant_name="Honeywell")
        self.s1 = AutomatedSystem.objects.create(
            autosystem_name="S1", system_class=self.cls, vendor=self.v1,
            system_status="active", product_type="software", creator_id=self.user,
        )
        self.s2 = AutomatedSystem.objects.create(
            autosystem_name="S2", system_class=self.cls, vendor=self.v2,
            system_status="planned", product_type="hardware", creator_id=self.user,
        )
        self.client_api = APIClient()

    def _names(self, params):
        resp = self.client_api.get("/api/system/", params)
        self.assertEqual(resp.status_code, 200)
        return sorted(row["autosystem_name"] for row in resp.data)

    def test_api_filter_by_vendor(self):
        self.assertEqual(self._names({"vendor": self.v1.pk}), ["S1"])

    def test_api_filter_by_status(self):
        self.assertEqual(self._names({"system_status": "planned"}), ["S2"])

    def test_api_filter_by_product_type(self):
        self.assertEqual(self._names({"product_type": "hardware"}), ["S2"])

    def test_api_filters_combine_with_and(self):
        self.assertEqual(self._names({"vendor": self.v1.pk, "system_status": "active"}), ["S1"])
        self.assertEqual(self._names({"vendor": self.v1.pk, "system_status": "planned"}), [])

    def test_api_multiselect_vendor_is_or(self):
        resp = self.client_api.get(f"/api/system/?vendor={self.v1.pk}&vendor={self.v2.pk}")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(sorted(r["autosystem_name"] for r in resp.data), ["S1", "S2"])
