"""Signal helpers."""
from django.apps import apps as global_apps
from django.db.models.signals import post_save
from django.dispatch import receiver
from nautobot.dcim.models import Platform
from nautobot.extras.models import Job
from nautobot_golden_config import models


def post_migrate_create_statuses(sender, apps=global_apps, **kwargs):  # pylint: disable=unused-argument
    """Callback function for post_migrate() -- create Status records."""
    Status = apps.get_model("extras", "Status")  # pylint: disable=invalid-name
    ContentType = apps.get_model("contenttypes", "ContentType")  # pylint: disable=invalid-name
    for status_config in [
        {
            "name": "Approved",
            "slug": "approved",
            "defaults": {
                "description": "Config plan is approved",
                "color": "4caf50",  # Green
            },
        },
        {
            "name": "Not Approved",
            "slug": "not-approved",
            "defaults": {
                "description": "Config plan is not approved",
                "color": "f44336",  # Red
            },
        },
    ]:
        status, _ = Status.objects.get_or_create(**status_config)
        status.content_types.add(ContentType.objects.get_for_model(models.ConfigPlan))


def post_migrate_create_job_button(sender, apps=global_apps, **kwargs):  # pylint: disable=unused-argument
    """Callback function for post_migrate() -- create JobButton records."""
    JobButton = apps.get_model("extras", "JobButton")  # pylint: disable=invalid-name
    Job = apps.get_model("extras", "Job")  # pylint: disable=invalid-name
    ContentType = apps.get_model("contenttypes", "ContentType")  # pylint: disable=invalid-name
    configplan_type = ContentType.objects.get_for_model(models.ConfigPlan)
    job_button_config = {
        "name": "Deploy Config Plan",
        "job": Job.objects.get(job_class_name="DeployConfigPlanJobButtonReceiver"),
        "defaults": {
            "text": "Deploy",
            "button_class": "primary",
        },
    }
    jobbutton, _ = JobButton.objects.get_or_create(**job_button_config)
    jobbutton.content_types.set([configplan_type])


def post_migrate_default_enabled_configplan_jobs(sender, apps=global_apps, **kwargs):  # pylint: disable=unused-argument
    """Signal to enable ConfigPlan job be default."""
    cp_job = Job.objects.get(name="Generate Config Plans")
    cp_job.enabled = True
    cp_job.save()


@receiver(post_save, sender=models.ConfigCompliance)
def config_compliance_platform_cleanup(sender, instance, **kwargs):  # pylint: disable=unused-argument
    """Signal helper to delete any orphaned ConfigCompliance objects. Caused by device platform changes."""
    cc_wrong_platform = models.ConfigCompliance.objects.filter(device=instance.device).filter(
        rule__platform__in=Platform.objects.exclude(slug=instance.device.platform.slug)
    )
    if cc_wrong_platform.count() > 0:
        cc_wrong_platform.delete()
