"""Added content to the device model view for config compliance."""

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count, Q
from django.urls import reverse
from nautobot.extras.plugins import PluginTemplateExtension

from nautobot_golden_config.models import ConfigCompliance, GoldenConfig
from nautobot_golden_config.utilities.constant import CONFIG_FEATURES, ENABLE_COMPLIANCE


class ConfigComplianceDeviceCheck(PluginTemplateExtension):  # pylint: disable=abstract-method
    """App extension class for config compliance."""

    model = "dcim.device"

    @property
    def device(self):
        """Device presented in detail view."""
        return self.context["object"]

    def right_page(self):
        """Content to add to the configuration compliance."""
        comp_obj = ConfigCompliance.objects.filter(device=self.device).values("rule__feature__name", "compliance")
        if not comp_obj:
            return ""
        extra_context = {
            "compliance": comp_obj,
            "device": self.device,
            "template_type": "devicetab",
        }
        return self.render(
            "nautobot_golden_config/content_template.html",
            extra_context=extra_context,
        )

    def detail_tabs(self):
        """Add a Configuration Compliance tab to the Device detail view if the Configuration Compliance associated to it."""
        try:
            if ConfigCompliance.objects.filter(device=self.device):
                return [
                    {
                        "title": "Configuration Compliance",
                        "url": reverse(
                            "plugins:nautobot_golden_config:configcompliance_devicetab",
                            kwargs={"pk": self.device.pk},
                        ),
                    }
                ]
        except ObjectDoesNotExist:
            return []

        return []


class ConfigComplianceLocationCheck(PluginTemplateExtension):  # pylint: disable=abstract-method
    """App extension class for config compliance."""

    model = "dcim.location"

    def get_locations(self):
        """Get location tree of object."""
        location = self.context["object"]
        locations = list(location.descendants())
        locations.append(location)
        return locations

    def right_page(self):
        """Content to add to the configuration compliance."""
        comp_obj = (
            ConfigCompliance.objects.values("rule__feature__name")
            .filter(device__location__in=self.get_locations())
            .annotate(
                count=Count("rule__feature__name"),
                compliant=Count("rule__feature__name", filter=Q(compliance=True)),
                non_compliant=Count("rule__feature__name", filter=~Q(compliance=True)),
            )
            .order_by("rule__feature__name")
            .values("rule__feature__name", "compliant", "non_compliant")
        )
        if not comp_obj:
            return ""
        extra_context = {"compliance": comp_obj, "template_type": "location"}
        return self.render(
            "nautobot_golden_config/content_template.html",
            extra_context=extra_context,
        )


class ConfigDeviceDetails(PluginTemplateExtension):  # pylint: disable=abstract-method
    """App extension class for config compliance."""

    model = "dcim.device"

    def get_device(self):
        """Get device object."""
        return self.context["object"]

    def right_page(self):
        """Content to add to the configuration compliance."""
        device = self.get_device()
        golden_config = GoldenConfig.objects.filter(device=device).first()
        if not golden_config:
            return ""
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


class ConfigComplianceTenantCheck(PluginTemplateExtension):  # pylint: disable=abstract-method
    """App extension class for config compliance."""

    model = "tenancy.tenant"

    def get_tenant(self):
        """Get tenant object."""
        return self.context["object"]

    def right_page(self):
        """Content to add to the configuration compliance."""
        comp_obj = (
            ConfigCompliance.objects.values("rule__feature__name")
            .filter(device__tenant=self.get_tenant().id)
            .annotate(
                count=Count("rule__feature__name"),
                compliant=Count("rule__feature__name", filter=Q(compliance=True)),
                non_compliant=Count("rule__feature__name", filter=~Q(compliance=True)),
            )
            .order_by("rule__feature__name")
            .values("rule__feature__name", "compliant", "non_compliant")
        )
        if not comp_obj:
            return ""
        extra_context = {"compliance": comp_obj, "template_type": "location"}
        return self.render(
            "nautobot_golden_config/content_template.html",
            extra_context=extra_context,
        )


extensions = [ConfigDeviceDetails]
if ENABLE_COMPLIANCE:
    extensions.append(ConfigComplianceDeviceCheck)
    extensions.append(ConfigComplianceLocationCheck)
    extensions.append(ConfigComplianceTenantCheck)


template_extensions = extensions
