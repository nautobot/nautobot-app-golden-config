"""Added content to the device model view for config compliance."""

from django.db.models import Count, Q
from nautobot.apps.ui import DistinctViewTab, TemplateExtension

from nautobot_golden_config.models import ConfigCompliance, GoldenConfig, GoldenConfigSetting


class ConfigComplianceDeviceCheck(TemplateExtension):  # pylint: disable=abstract-method
    """App extension class for config compliance."""

    model = "dcim.device"

    object_detail_tabs = [
        DistinctViewTab(
            weight=100,
            tab_id="device_tab",
            label="Configuration Compliance",
            url_name="plugins:nautobot_golden_config:configcompliance_devicetab",
            related_object_attribute="configcompliance_set",
            hide_if_empty=True,
        )
    ]

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


class ConfigComplianceLocationCheck(TemplateExtension):  # pylint: disable=abstract-method
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


class ConfigDeviceDetails(TemplateExtension):  # pylint: disable=abstract-method
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
        # A device that has left the scope of every Setting keeps its stored configs viewable; only the
        # actions that need a Setting to run (SoT aggregation and postprocessing) are hidden.
        gc_setting = GoldenConfigSetting.objects.get_for_device(device)
        extra_context = {
            "device": device,
            "golden_config": golden_config,
            "template_type": "device-configs",
            "config_features": {
                "intended": getattr(gc_setting, "enable_intended", True),
                "compliance": getattr(gc_setting, "enable_compliance", True),
                "backup": getattr(gc_setting, "enable_backup", True),
                "sotagg": getattr(gc_setting, "enable_sotagg", False),
                "postprocessing": getattr(gc_setting, "enable_postprocessing", False),
            },
        }
        return self.render(
            "nautobot_golden_config/content_template.html",
            extra_context=extra_context,
        )


class ConfigComplianceTenantCheck(TemplateExtension):  # pylint: disable=abstract-method
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


template_extensions = [
    ConfigDeviceDetails,
    ConfigComplianceDeviceCheck,
    ConfigComplianceLocationCheck,
    ConfigComplianceTenantCheck,
]
