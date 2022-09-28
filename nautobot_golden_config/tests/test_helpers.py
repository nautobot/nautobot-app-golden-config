"""Unit tests for nautobot_golden_config helpers."""
import os
from unittest import mock
import jinja2

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.contrib.contenttypes.models import ContentType

from nautobot.extras.models import SecretsGroup, Secret, SecretsGroupAssociation
from nautobot.extras.choices import SecretsGroupAccessTypeChoices, SecretsGroupSecretTypeChoices
from nautobot.users.models import ObjectPermission

from nautobot_golden_config.utilities.config_postprocessing import (
    get_secret_by_secret_group_slug,
    render_secrets,
    get_config_postprocessing,
)
from nautobot_golden_config.models import GoldenConfig
from nautobot_golden_config.utilities.constant import PLUGIN_CFG

from .conftest import create_device


# Use the proper swappable User model
User = get_user_model()


class GetSecretFilterTestCase(TestCase):
    """Test Get Secrets filters."""

    def setUp(self):
        """Setup Object."""
        self.device = create_device()
        self.configs = GoldenConfig.objects.create(device=self.device)

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

        self.user_admin = User.objects.create(username="user_admin", is_superuser=True)

        self.user_2 = User.objects.create(username="User_2")

        self.permission, _ = ObjectPermission.objects.update_or_create(
            name="my_permissions",
            defaults={"actions": ["view"]},
        )
        self.permission.object_types.set(
            [
                ContentType.objects.get(app_label="extras", model="secretsgroup"),
            ]
        )
        self.permission.validated_save()

    @mock.patch.dict(os.environ, {"NAUTOBOT_TEST_ENVIRONMENT_VARIABLE": "supersecretvalue"})
    def test_get_secret_by_secret_group_slug_superuser(self):
        """A super user admin should get the secret rendered."""
        self.assertEqual(
            get_secret_by_secret_group_slug(
                self.user_admin, self.secrets_group.slug, SecretsGroupSecretTypeChoices.TYPE_SECRET
            ),
            "supersecretvalue",
        )

    @mock.patch.dict(os.environ, {"NAUTOBOT_TEST_ENVIRONMENT_VARIABLE": "supersecretvalue"})
    def test_get_secret_by_secret_group_slug_user_without_permission(self):
        """A normal user without permissions, should not get the secret rendered."""
        self.assertEqual(
            get_secret_by_secret_group_slug(
                self.user_2, self.secrets_group.slug, SecretsGroupSecretTypeChoices.TYPE_SECRET
            ),
            f"You have no permission to read this secret {self.secrets_group.slug}.",
        )

    @mock.patch.dict(os.environ, {"NAUTOBOT_TEST_ENVIRONMENT_VARIABLE": "supersecretvalue"})
    def test_get_secret_by_secret_group_slug_user_with_permission(self):
        """A normal user with permissions, should get the secret rendered."""
        self.permission.users.set([self.user_2])
        self.permission.validated_save()

        self.assertEqual(
            get_secret_by_secret_group_slug(
                self.user_2, self.secrets_group.slug, SecretsGroupSecretTypeChoices.TYPE_SECRET
            ),
            "supersecretvalue",
        )

    @mock.patch.dict(os.environ, {"NAUTOBOT_TEST_ENVIRONMENT_VARIABLE": "supersecretvalue"})
    @mock.patch(
        "nautobot_golden_config.utilities.config_postprocessing._get_device_agg_data",
        mock.MagicMock(return_value={"group_slug": "secrets-group-1"}),
    )
    def test_get_secret_end_to_end(self):
        """This test will take an initial Jinja template and do the double rendering to demonstrate
        the end to end experience.
        """
        initial_template = "{% raw %}{{ group_slug | get_secret_by_secret_group_slug('secret') }}{% endraw %}"

        # This simulates the first rendering to generate the Intended configuration
        jinja_env = jinja2.Environment(autoescape=True)
        template = jinja_env.from_string(initial_template)
        intended_config = template.render({})
        self.assertEqual(
            intended_config,
            "{{ group_slug | get_secret_by_secret_group_slug('secret') }}",
        )

        mock_request = mock.Mock()
        mock_request.user = self.user_admin

        self.assertEqual(
            render_secrets(intended_config, self.configs, mock_request),
            "supersecretvalue",
        )

    def test_config_postprocessing_with_wrong_function_name(self):
        """Test that postprocessing when called with an unexistent function name, raises ValueError exception."""
        PLUGIN_CFG["postprocessing_subscribed"] = ["whatever"]
        self.configs.intended_config = "something"

        with self.assertRaises(ValueError):
            get_config_postprocessing(
                self.configs,
                mock.Mock(),
            )
