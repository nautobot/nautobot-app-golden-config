"""Remove the retired `Approved` and `Not Approved` Status records, if unused.

After migration 0033, no ConfigPlan should reference either status. We defensively
verify that, then unbind the records from the ConfigPlan ContentType and delete
them if no other content type references them. If either condition fails, we leave
the Status records alone and let an admin clean up manually.
"""

from django.db import migrations

RETIRED_STATUSES = ("Approved", "Not Approved")


def remove_unused_statuses(apps, schema_editor):
    ConfigPlan = apps.get_model("nautobot_golden_config", "ConfigPlan")
    Status = apps.get_model("extras", "Status")
    ContentType = apps.get_model("contenttypes", "ContentType")

    ct_configplan = ContentType.objects.get_for_model(ConfigPlan)

    for name in RETIRED_STATUSES:
        try:
            status = Status.objects.get(name=name)
        except Status.DoesNotExist:
            continue

        if ConfigPlan.objects.filter(status=status).exists():
            # Defensive: 0033 should have nulled all references already.
            continue

        status.content_types.remove(ct_configplan)
        if not status.content_types.exists():
            status.delete()


def restore_statuses(apps, schema_editor):
    """Re-create the retired Status records and re-associate them with ConfigPlan."""
    ConfigPlan = apps.get_model("nautobot_golden_config", "ConfigPlan")
    Status = apps.get_model("extras", "Status")
    ContentType = apps.get_model("contenttypes", "ContentType")

    ct_configplan = ContentType.objects.get_for_model(ConfigPlan)

    defaults = {
        "Approved": {"description": "Config plan is approved", "color": "4caf50"},
        "Not Approved": {"description": "Config plan is not approved", "color": "f44336"},
    }
    for name, fields in defaults.items():
        status, _ = Status.objects.get_or_create(name=name, defaults=fields)
        status.content_types.add(ct_configplan)


class Migration(migrations.Migration):
    dependencies = [
        ("nautobot_golden_config", "0033_configplan_force_reapproval"),
    ]

    operations = [
        migrations.RunPython(remove_unused_statuses, restore_statuses),
    ]
