from django.test import TestCase
from django.urls import reverse


class HealthCheckTests(TestCase):
    def test_liveness(self):
        response = self.client.get(reverse("core:health-live"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_readiness(self):
        response = self.client.get(reverse("core:health-ready"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["checks"]["database"], "ok")
