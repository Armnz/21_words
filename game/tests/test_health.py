from django.test import Client, TestCase
from rest_framework import status


class HealthCheckTestCase(TestCase):
    """Test suite for health check endpoint."""

    def setUp(self):
        """Set up test client."""
        self.client = Client()

    def test_health_endpoint_returns_ok(self):
        """Test that GET /api/health/ returns status ok."""
        response = self.client.get("/api/health/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_health_endpoint_content_type(self):
        """Test that health endpoint returns JSON content."""
        response = self.client.get("/api/health/")
        self.assertEqual(response["Content-Type"], "application/json")
