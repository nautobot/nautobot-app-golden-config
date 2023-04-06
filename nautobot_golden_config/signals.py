from typing import Optional

from django.db.models import Q
from django.db.models.signals import pre_save, post_delete, post_save
from django.dispatch import receiver

from nautobot.dcim.models import Device
from nautobot.extras.models import DynamicGroup
from nautobot.extras.querysets import ConfigContextModelQuerySet

from .models import GoldenConfig, GoldenConfigSetting


def create_empty_golden_config_entries_added_to_scope(dynamic_group_members: ConfigContextModelQuerySet) -> None:
    """
    Add placeholder entries to `GoldenConfig` table.

    As DynamicGroups associated with GoldenConfigSettings are modified, the
    Devices newly associated with the GoldenConfig table need to have entries
    added to the table. This creates only Devices in `dynamic_group_members`
    that are not currently in the GoldenConfig table.

    Args:
        dynamic_group_members: A queryset of Devices included by the updated DynamicGroup.
    """
    # generate a queryset of Devices that currently have corresponding entries in GoldenConfig
    golden_config_devices = Device.objects.filter(goldenconfig__in=GoldenConfig.objects.all())
    # create GoldenConfig entries only for devices missing from the table
    for device in dynamic_group_members.difference(golden_config_devices):
        GoldenConfig.objects.create(device=device)


def delete_golden_config_entries_removed_from_scope(
    golden_config_device_queryset: Optional[ConfigContextModelQuerySet] = None,
    setting_to_exclude: Optional[GoldenConfigSetting] = None,
):
    """
    Delete GoldenConfig entries for Devices removed from DynamicGroup.

    As DynamicGroups associated with GoldenConfigSettings are modified, the
    Devices that no longer associated with the GoldenConfig table need to be
    removed from GoldenConfig. This deletes those entries from the GoldenConfig
    table.

    Args:
        golden_config_device_queryset: A prepopulated queryset of Devices in GoldenConfig.
            This allows for DynamicGroup members being included for an update
            that is in the process of being saved to the database, but has not
            yet been completed (pre_save signal). The GoldenConfigSetting that
            is associated with the DynamicGroup should be passed as
            `setting_to_exclude`. If this is not passed, the default will use an
            empty queryset.
        setting_to_exclude: A setting that should have its DynamicGroup excluded.
            This allows for a setting to have its DynamicGroup members excluded
            for an update that is in the process of being saved to the database,
            but has not yet been completed (pre_save signal). The modified
            DynamicGroup should have its updated members passed as
            `golden_config_device_queryset`. The default is to not modify the
            final queryset.
    """
    golden_config_dynamic_groups = DynamicGroup.objects.filter(golden_config_setting__isnull=False)

    # Prevent exception in case all GoldenConfig DynamicGroups have been deleted
    if not golden_config_dynamic_groups:
        return

    # default device queryset to an empty queryset
    if golden_config_device_queryset is None:
        golden_config_device_queryset = golden_config_dynamic_groups.first().members.none()

    # exclude DynamicGroup that has been included as part of `golden_config_device_queryset`
    if setting_to_exclude is not None:
        golden_config_dynamic_groups = golden_config_dynamic_groups.exclude(golden_config_setting=setting_to_exclude)

    # generate queryset of devices that should have corresponding entries in GoldenConfig
    for dynamic_group in golden_config_dynamic_groups:
        golden_config_device_queryset = golden_config_device_queryset | dynamic_group.members

    GoldenConfig.objects.exclude(device__in=golden_config_device_queryset).delete()


@receiver(pre_save, sender=GoldenConfigSetting)
def refresh_golden_config_table_from_golden_config_setting_dynamic_group_update(sender, instance, **kwargs):
    """Django signal reciever to update GoldenConfig entries upon GoldenConfigSetting updates."""
    # check if setting has been modified or created
    modified = GoldenConfigSetting.objects.filter(pk=instance.pk).exists()
    if not modified:
        create_empty_golden_config_entries_added_to_scope(instance.dynamic_group.members)
    else:
        # check if dynamic_group has changed
        existing_goldenconfig_setting = GoldenConfigSetting.objects.get(pk=instance.pk)
        dynamic_group_changed = existing_goldenconfig_setting.dynamic_group != instance.dynamic_group

        # update Golden Config entries when dynamic_group has been changed
        if dynamic_group_changed:
            delete_golden_config_entries_removed_from_scope(
                golden_config_device_queryset=instance.dynamic_group.members,  # need to start with DynamicGroup as defined in instance (this has the update DynamicGroup)
                setting_to_exclude=instance,  # need to exclude the current instance since save has not happened and it will have outdated members
            )
            create_empty_golden_config_entries_added_to_scope(instance.dynamic_group.members)


@receiver(post_delete, sender=GoldenConfigSetting)
def remove_golden_config_entries_from_golden_config_setting_deletion(sender, instance, **kwargs):
    """Django signal reciever to remove GoldenConfig entries upon GoldenConfigSetting deletion."""
    delete_golden_config_entries_removed_from_scope()


@receiver(post_save, sender=DynamicGroup)
def refresh_golden_config_table_from_dynamic_group(sender, instance, created, **kwargs):
    """Django signal reciever to update GoldenConfig enties upon DynamicGroup updates."""
    # newly created dynamic_groups cannot yet be associated with a GoldenConfigSetting instance
    if created:
        return

    # only update GoldenConfig table if DynamicGroup object is used by GoldenConfigSettings
    if DynamicGroup.objects.filter(golden_config_setting__isnull=False, pk=instance.pk).exists():
        delete_golden_config_entries_removed_from_scope()
        create_empty_golden_config_entries_added_to_scope(instance.members)
