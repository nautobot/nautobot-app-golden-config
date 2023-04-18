"""Signal helpers."""

from django.db.models.signals import pre_save
from django.dispatch import receiver
from nautobot.dcim.models import Platform
from nautobot_golden_config import models


@receiver(pre_save, sender=models.ConfigCompliance)
def config_compliance_platform_cleanup(sender, instance, **kwargs):
    """Signal helper to delete any orphaned ConfigCompliance objects. Caused by device platform changes."""
    cc_wrong_platform = models.ConfigCompliance.objects.exclude(
        device=instance.device, rule__platform=Platform.objects.get(slug=instance.device.platform.slug)
    )
    if cc_wrong_platform.count() > 0:
        cc_wrong_platform.delete()
