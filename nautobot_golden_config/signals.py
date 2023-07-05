"""Signal helpers."""
from django.apps import apps as global_apps
from django.db.models.signals import post_save
from django.dispatch import receiver
from nautobot.dcim.models import Platform
from nautobot_golden_config import models


def post_migrate_create_statuses(sender, apps=global_apps, **kwargs):  # pylint: disable=unused-argument
    """Callback function for post_migrate() -- create Status records."""
    Status = apps.get_model("extras", "Status")  # pylint: disable=invalid-name
    ContentType = apps.get_model("contenttypes", "ContentType")  # pylint: disable=invalid-name
    for status_config in [
        {
            "name": "Accepted",
            "slug": "accepted",
            "defaults": {
                "description": "Config plan is accepted",
                "color": "4caf50",  # Green
            },
        },
        {
            "name": "Not Accepted",
            "slug": "not-accepted",
            "defaults": {
                "description": "Config plan is not accepted",
                "color": "f44336",  # Red
            },
        },
    ]:
        status, _ = Status.objects.get_or_create(**status_config)
        status.content_types.add(ContentType.objects.get_for_model(models.ConfigPlan))


@receiver(post_save, sender=models.ConfigCompliance)
def config_compliance_platform_cleanup(sender, instance, **kwargs):  # pylint: disable=unused-argument
    """Signal helper to delete any orphaned ConfigCompliance objects. Caused by device platform changes."""
    cc_wrong_platform = models.ConfigCompliance.objects.filter(device=instance.device).filter(
        rule__platform__in=Platform.objects.exclude(slug=instance.device.platform.slug)
    )
    if cc_wrong_platform.count() > 0:
        cc_wrong_platform.delete()
