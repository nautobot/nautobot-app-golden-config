# Generated by Django 3.2.14 on 2022-07-11 14:18

from django.db import migrations, models
from django.utils.text import slugify
import django.db.models.deletion


def create_dynamic_groups(apps, schedma_editor):
    """Migrate DynamicGroups from instance.scope ."""
    model = apps.get_model("extras.DynamicGroup")
    content_type = apps.get_model("contenttypes.ContentType").objects.get(app_label="dcim", model="device")
    qs = apps.get_model("nautobot_golden_config.GoldenConfigSetting").objects.all()
    for i in qs:
        if i.scope:
            name = f"GoldenConfigSetting {i.name} scope"
            d_group = model.objects.create(
                name=name,
                slug=slugify(name),
                filter=i.scope,
                content_type=content_type,
                description="Automatically generated for nautobot_golden_config version 2.0.0.",
            )
            i.dynamic_group = d_group
            i.save()


class Migration(migrations.Migration):

    dependencies = [
        ("nautobot_golden_config", "0019_convert_dynamicgroup_part_1"),
    ]

    operations = [
        migrations.RunPython(code=create_dynamic_groups),
    ]
