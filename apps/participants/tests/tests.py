from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from apps.participants.models import Participant


class ParticipantsWebEndpointTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="user", password="password")
        self.participant = Participant.objects.create(participant_name="ООО Вендор")

    def test_participant_list_page_is_available(self):
        response = self.client.get("/participants/")
        self.assertEqual(response.status_code, 200)

    def test_participant_list_supports_search(self):
        response = self.client.get("/participants/", {"search": "вендор"})
        self.assertEqual(response.status_code, 200)

    def test_participant_detail_page_is_available(self):
        response = self.client.get(f"/participants/{self.participant.pk}/")
        self.assertEqual(response.status_code, 200)

    def test_participant_create_page_requires_authentication(self):
        response = self.client.get("/participants/create/")
        self.assertEqual(response.status_code, 302)

    def test_authenticated_participant_crud_endpoints(self):
        self.client.force_login(self.user)

        response = self.client.get("/participants/create/")
        self.assertEqual(response.status_code, 200)

        response = self.client.post("/participants/create/", {
            "participant_name": "ООО Интегратор",
        })
        self.assertEqual(response.status_code, 302)
        created = Participant.objects.get(participant_name="ООО Интегратор")

        response = self.client.get(f"/participants/{created.pk}/edit/")
        self.assertEqual(response.status_code, 200)

        response = self.client.post(f"/participants/{created.pk}/edit/", {
            "participant_name": "ООО Интегратор 2",
        })
        self.assertEqual(response.status_code, 302)
        created.refresh_from_db()
        self.assertEqual(created.participant_name, "ООО Интегратор 2")

        response = self.client.post(f"/participants/{created.pk}/delete/")
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Participant.objects.filter(pk=created.pk).exists())


class ParticipantsApiEndpointTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="api-user", password="password")
        self.participant = Participant.objects.create(participant_name="ООО Вендор")
        self.api_client = APIClient()

    def test_participant_api_list_and_detail_are_public(self):
        response = self.api_client.get("/api/participants/", {"search": "вендор"})
        self.assertEqual(response.status_code, 200)

        response = self.api_client.get(f"/api/participants/{self.participant.pk}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], self.participant.pk)

    def test_participant_api_create_requires_authentication(self):
        response = self.api_client.post("/api/participants/", {
            "participant_name": "ООО API",
        }, format="json")
        self.assertIn(response.status_code, (401, 403))

    def test_authenticated_participant_api_crud(self):
        self.api_client.force_authenticate(user=self.user)

        response = self.api_client.post("/api/participants/", {
            "participant_name": "ООО API",
        }, format="json")
        self.assertEqual(response.status_code, 201)
        participant_id = response.data["id"]

        response = self.api_client.patch(f"/api/participants/{participant_id}/", {
            "participant_name": "ООО API 2",
        }, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["participant_name"], "ООО API 2")

        response = self.api_client.delete(f"/api/participants/{participant_id}/")
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Participant.objects.filter(pk=participant_id).exists())
