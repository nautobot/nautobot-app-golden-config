"""Added content to the device model view for config compliance."""
from django.db.models import Count, Q
from nautobot.extras.plugins import PluginTemplateExtension

from .models import ConfigCompliance, GoldenConfiguration
from .utilities.constant import ENABLE_COMPLIANCE, CONFIG_FEATURES
from .utilities.helper import get_allowed_os_from_nested


class ConfigComplianceDeviceCheck(PluginTemplateExtension):  # pylint: disable=abstract-method
    """Plugin extension class for config compliance."""

    model = "dcim.device"

    def get_device(self):
        """Get device object."""
        return self.context["object"]

    def right_page(self):
        """Content to add to the configuration compliance."""
        comp_obj = (
            ConfigCompliance.objects.filter(**get_allowed_os_from_nested())
            .filter(device=self.get_device())
            .values("feature", "compliance")
        )
        extra_context = {
            "compliance": comp_obj,
            "device": self.get_device(),
            "template_type": "device-compliance",
        }
        return self.render(
            "nautobot_golden_config/content_template.html",
            extra_context=extra_context,
        )


class ConfigComplianceSiteCheck(PluginTemplateExtension):  # pylint: disable=abstract-method
    """Plugin extension class for config compliance."""

    model = "dcim.site"

    def get_site_slug(self):
        """Get site object."""
        return self.context["object"]

    def right_page(self):
        """Content to add to the configuration compliance."""
        comp_obj = (
            ConfigCompliance.objects.values("feature")
            .filter(**get_allowed_os_from_nested())
            .filter(device__site__slug=self.get_site_slug().slug)
            .annotate(
                compliant=Count("feature", filter=Q(compliance=True)),
                non_compliant=Count("feature", filter=~Q(compliance=True)),
            )
            .values("feature", "compliant", "non_compliant")
        )

        extra_context = {"compliance": comp_obj, "template_type": "site"}
        return self.render(
            "nautobot_golden_config/content_template.html",
            extra_context=extra_context,
        )


class ConfigDeviceDetails(PluginTemplateExtension):  # pylint: disable=abstract-method
    """Plugin extension class for config compliance."""

    model = "dcim.device"

    def get_device(self):
        """Get device object."""
        return self.context["object"]

    def right_page(self):
        """Content to add to the configuration compliance."""
        golden_config = (
            GoldenConfiguration.objects.filter(**get_allowed_os_from_nested()).filter(device=self.get_device()).first()
        )
        extra_context = {
            "device": self.get_device(),  # device,
            "golden_config": golden_config,
            "template_type": "device-configs",
            "config_features": CONFIG_FEATURES,
        }
        return self.render(
            "nautobot_golden_config/content_template.html",
            extra_context=extra_context,
        )


extensions = [ConfigDeviceDetails]
if ENABLE_COMPLIANCE:
    extensions.append(ConfigComplianceDeviceCheck)
    extensions.append(ConfigComplianceSiteCheck)

template_extensions = extensions
