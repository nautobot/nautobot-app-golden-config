"""Unit tests for nautobot_golden_config."""
from django.contrib.auth import get_user_model

from django.urls import reverse
from rest_framework import status

from nautobot.utilities.testing import APITestCase


User = get_user_model()


class GoldenConfigAPITest(APITestCase):  # pylint: disable=too-many-ancestors
    """Test the ConfigCompliance API."""

    def test_device_list(self):
        """Verify that devices can be listed."""
        url = reverse("dcim-api:device-list")
        self.add_permissions("dcim.view_device")
        response = self.client.get(url, **self.header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 0)
