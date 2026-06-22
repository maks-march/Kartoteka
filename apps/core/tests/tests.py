from django.test import TestCase


class CoreEndpointTests(TestCase):
    def test_hub_page_is_available(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
