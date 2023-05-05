"""Signal helpers."""

from django.db.models.signals import post_save
from django.dispatch import receiver
from nautobot.dcim.models import Platform
from nautobot_golden_config import models


@receiver(post_save, sender=models.ConfigCompliance)
def config_compliance_platform_cleanup(sender, instance, **kwargs):  # pylint: disable=unused-argument
    """Signal helper to delete any orphaned ConfigCompliance objects. Caused by device platform changes."""
    cc_wrong_platform = models.ConfigCompliance.objects.filter(device=instance.device).filter(
        rule__platform__in=Platform.objects.exclude(slug=instance.device.platform.slug)
    )
    if cc_wrong_platform.count() > 0:
        cc_wrong_platform.delete()
