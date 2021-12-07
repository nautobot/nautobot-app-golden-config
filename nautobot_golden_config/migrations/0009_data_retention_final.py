# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def convert_many_repos(apps, schema_editor):
    """
    Add the current `backup_repository` and `intended_repository` objects
    to the `many_to_many` additional intermediary attritbute to retain data.`
    """
    GoldenConfigSetting = apps.get_model("nautobot_golden_config", "GoldenConfigSetting")

    settings_obj = GoldenConfigSetting.objects.first()
    if settings_obj.backup_repositories.all():
        [settings_obj.backup_repository.add(backup_repo) for backup_repo in settings_obj.backup_repositories.all()]
    if settings_obj.intended_repositories.all():
        [
            settings_obj.intended_repository.add(intended_repo)
            for intended_repo in settings_obj.intended_repositories.all()
        ]


class Migration(migrations.Migration):

    dependencies = [
        ("nautobot_golden_config", "0008_convert_many"),
    ]

    operations = [
        migrations.RunPython(convert_many_repos),
    ]
