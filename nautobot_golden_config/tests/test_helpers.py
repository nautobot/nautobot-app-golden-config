"""Unit tests for nautobot_golden_config helpers."""

import os
from importlib import import_module
from unittest import mock

import jinja2
from django.conf import settings as django_settings
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import RequestFactory, TestCase
from nautobot.apps.choices import SecretsGroupAccessTypeChoices, SecretsGroupSecretTypeChoices
from nautobot.dcim.models import Device
from nautobot.extras.models import DynamicGroup, Secret, SecretsGroup, SecretsGroupAssociation
from nautobot.users.models import ObjectPermission

from nautobot_golden_config.models import GoldenConfig, GoldenConfigSetting
from nautobot_golden_config.utilities.config_postprocessing import (
    get_config_postprocessing,
    get_secret_by_secret_group_name,
    render_secrets,
)
from nautobot_golden_config.utilities.constant import PLUGIN_CFG
from nautobot_golden_config.utilities.helper import add_intended_requirements_message

from .conftest import create_device

# Use the proper swappable User model
User = get_user_model()


class GetSecretFilterTestCase(TestCase):
    """Test Get Secrets filters."""

    def setUp(self):
        """Setup Object."""
        self.device = create_device()
        self.configs = GoldenConfig.objects.create(device=self.device)

        self.secrets_group = SecretsGroup(name="Secrets Group 1")
        self.secrets_group.validated_save()

        self.environment_secret = Secret.objects.create(
            name="Environment Variable Secret",
            provider="environment-variable",
            parameters={"variable": "NAUTOBOT_TEST_ENVIRONMENT_VARIABLE"},
        )

        SecretsGroupAssociation.objects.create(
            secrets_group=self.secrets_group,
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
    def test_get_secret_by_secret_group_name_superuser(self):
        """A super user admin should get the secret rendered."""
        self.assertEqual(
            get_secret_by_secret_group_name(
                self.user_admin,
                self.secrets_group.name,
                SecretsGroupSecretTypeChoices.TYPE_SECRET,
            ),
            "supersecretvalue",
        )

    @mock.patch.dict(os.environ, {"NAUTOBOT_TEST_ENVIRONMENT_VARIABLE": "supersecretvalue"})
    def test_get_secret_by_secret_group_name_user_without_permission(self):
        """A normal user without permissions, should not get the secret rendered."""
        self.assertEqual(
            get_secret_by_secret_group_name(
                self.user_2,
                self.secrets_group.name,
                SecretsGroupSecretTypeChoices.TYPE_SECRET,
            ),
            f"You have no permission to read this secret {self.secrets_group.name}.",
        )

    @mock.patch.dict(os.environ, {"NAUTOBOT_TEST_ENVIRONMENT_VARIABLE": "supersecretvalue"})
    def test_get_secret_by_secret_group_name_user_with_permission(self):
        """A normal user with permissions, should get the secret rendered."""
        self.permission.users.set([self.user_2])
        self.permission.validated_save()

        self.assertEqual(
            get_secret_by_secret_group_name(
                self.user_2,
                self.secrets_group.name,
                SecretsGroupSecretTypeChoices.TYPE_SECRET,
            ),
            "supersecretvalue",
        )

    def test_render_secrets_without_graphql_query(self):
        """A Setting with no GraphQL query, or no Setting at all, renders the config with no device data."""
        mock_request = mock.Mock()
        mock_request.user = self.user_admin
        for setting in (mock.Mock(sot_agg_query=None), None):
            with self.subTest(setting=setting):
                with mock.patch(
                    "nautobot_golden_config.models.GoldenConfigSetting.objects.get_for_device",
                    return_value=setting,
                ):
                    self.assertEqual(render_secrets("hostname router1", self.configs, mock_request), "hostname router1")

    @mock.patch.dict(os.environ, {"NAUTOBOT_TEST_ENVIRONMENT_VARIABLE": "supersecretvalue"})
    @mock.patch(
        "nautobot_golden_config.utilities.config_postprocessing._get_device_agg_data",
        mock.MagicMock(return_value={"group_name": "Secrets Group 1"}),
    )
    def test_get_secret_end_to_end(self):
        """This test will take an initial Jinja template and do the double rendering to demonstrate
        the end to end experience.
        """
        initial_template = "{% raw %}{{ group_name | get_secret_by_secret_group_name('secret') }}{% endraw %}"

        # This simulates the first rendering to generate the Intended configuration
        jinja_env = jinja2.Environment(autoescape=True)
        template = jinja_env.from_string(initial_template)
        intended_config = template.render({})
        self.assertEqual(
            intended_config,
            "{{ group_name | get_secret_by_secret_group_name('secret') }}",
        )

        mock_request = mock.Mock()
        mock_request.user = self.user_admin

        self.assertEqual(
            render_secrets(intended_config, self.configs, mock_request),
            "supersecretvalue",
        )

    @mock.patch(
        "nautobot_golden_config.models.GoldenConfigSetting.objects.get_for_device",
        mock.MagicMock(return_value=mock.Mock(enable_postprocessing=True)),
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

    def test_config_postprocessing_disabled_on_winning_setting(self):
        """Postprocessing returns the disabled message when the winning Setting has it off."""
        self.configs.intended_config = "something"
        with mock.patch(
            "nautobot_golden_config.models.GoldenConfigSetting.objects.get_for_device",
            mock.MagicMock(return_value=mock.Mock(enable_postprocessing=False)),
        ):
            result = get_config_postprocessing(self.configs, mock.Mock())
        self.assertIn("not enabled", result)

    def test_config_postprocessing_no_winning_setting(self):
        """Postprocessing returns the disabled message when the device has no winning Setting."""
        self.configs.intended_config = "something"
        with mock.patch(
            "nautobot_golden_config.models.GoldenConfigSetting.objects.get_for_device",
            mock.MagicMock(return_value=None),
        ):
            result = get_config_postprocessing(self.configs, mock.Mock())
        self.assertIn("not enabled", result)


class AddIntendedRequirementsMessageTestCase(TestCase):
    """Test the non-blocking warning for Settings that have Intended enabled but are incompletely configured."""

    def setUp(self):
        """Build a request with the messages framework attached."""
        GoldenConfigSetting.objects.all().delete()
        self.dynamic_group = DynamicGroup.objects.create(
            name="intended-warning-dg",
            content_type=ContentType.objects.get_for_model(Device),
            filter={},
        )
        self.request = RequestFactory().get("/")
        self.request.user = User.objects.create(username="intended-warning-admin", is_superuser=True)
        engine = import_module(django_settings.SESSION_ENGINE)
        self.request.session = engine.SessionStore()
        self.request._messages = FallbackStorage(self.request)  # pylint: disable=protected-access

    def _make_setting(self, **overrides):
        defaults = {
            "name": "intended-warning-setting",
            "slug": "intended-warning-setting",
            "weight": 1000,
            "dynamic_group": self.dynamic_group,
            "enable_intended": True,
        }
        defaults.update(overrides)
        return GoldenConfigSetting.objects.create(**defaults)

    def test_incomplete_intended_setting_emits_warning(self):
        """A Setting with Intended enabled but missing fields produces a single warning naming the Setting."""
        setting = self._make_setting()
        add_intended_requirements_message([setting], self.request)
        warnings = [str(message) for message in self.request._messages]  # pylint: disable=protected-access
        self.assertEqual(len(warnings), 1)
        self.assertIn(setting.name, warnings[0])
        self.assertIn("will not generate intended configurations", warnings[0])
        self.assertIn(f"/golden-config-setting/{setting.pk}/edit/", warnings[0])

    def test_warning_has_no_edit_link_for_user_who_cannot_edit(self):
        """A user without change permission sees the Setting named, but is not sent to an edit page."""
        self.request.user = User.objects.create(username="intended-warning-viewer")
        setting = self._make_setting()
        add_intended_requirements_message([setting], self.request)
        warnings = [str(message) for message in self.request._messages]  # pylint: disable=protected-access
        self.assertEqual(len(warnings), 1)
        self.assertIn(setting.name, warnings[0])
        self.assertNotIn("/edit/", warnings[0])

    def test_intended_disabled_setting_emits_no_warning(self):
        """A Setting with Intended disabled never warns, even with the intended fields blank."""
        setting = self._make_setting(enable_intended=False)
        add_intended_requirements_message([setting], self.request)
        warnings = list(self.request._messages)  # pylint: disable=protected-access
        self.assertEqual(warnings, [])
