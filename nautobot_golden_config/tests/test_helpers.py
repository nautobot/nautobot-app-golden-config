"""Unit tests for nautobot_golden_config helpers."""
import os
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase

from nautobot.extras.models import SecretsGroup, Secret, SecretsGroupAssociation
from nautobot.extras.choices import SecretsGroupAccessTypeChoices, SecretsGroupSecretTypeChoices

from nautobot_golden_config.utilities.helper import get_secret_by_secret_group_slug

# Use the proper swappable User model
User = get_user_model()


class GetSecretFilterTestCase(TestCase):
    """Test Get Secrets filters."""

    def setUp(self):
        """Setup Object."""
        self.secrets_group = SecretsGroup(name="Secrets Group 1", slug="secrets-group-1")
        self.secrets_group.validated_save()

        self.environment_secret = Secret.objects.create(
            name="Environment Variable Secret",
            slug="env-var",
            provider="environment-variable",
            parameters={"variable": "NAUTOBOT_TEST_ENVIRONMENT_VARIABLE"},
        )

        SecretsGroupAssociation.objects.create(
            group=self.secrets_group,
            secret=self.environment_secret,
            access_type=SecretsGroupAccessTypeChoices.TYPE_GENERIC,
            secret_type=SecretsGroupSecretTypeChoices.TYPE_SECRET,
        )

        self.user_admin_1 = User.objects.create(username="User_Admin_1", is_superuser=True)
        self.user_2 = User.objects.create(username="User_2")

    @mock.patch.dict(os.environ, {"NAUTOBOT_TEST_ENVIRONMENT_VARIABLE": "supersecretvalue"})
    def test_get_secret_by_secret_group_slug_superuser(self):
        """A super user admin should get the secret rendered."""
        self.assertEqual(
            get_secret_by_secret_group_slug(
                self.user_admin_1, self.secrets_group.slug, SecretsGroupSecretTypeChoices.TYPE_SECRET
            ),
            "supersecretvalue",
        )

    def test_get_secret_by_secret_group_slug_user_without_permission(self):
        """A normal user without permissions, should not get the secret rendered."""
        self.assertEqual(
            get_secret_by_secret_group_slug(
                self.user_2, self.secrets_group.slug, SecretsGroupSecretTypeChoices.TYPE_SECRET
            ),
            f"You have no permission to read this secret {self.secrets_group.slug}.",
        )

    # TODO: tests for user with permissions for the secret
