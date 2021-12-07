# -*- coding: utf-8 -*-
"""This file is meant to take the current ForeginKey relationship assosciated to
a single repository object from GoldenConfigSetting backup_repo and intended_repo
attribute and populate a temporary many_to_many attribute."""

from __future__ import unicode_literals

from django.db import models, migrations


def convert_many_repos(apps, schema_editor):
    """
    Add the current `backup_repository` and `intended_repository` objects
    to the `many_to_many` additional intermediary attritbute to retain data.`
    """
    GoldenConfigSetting = apps.get_model("nautobot_golden_config", "GoldenConfigSetting")

    settings_obj = GoldenConfigSetting.objects.first()

    settings_obj.backup_repositories.add(settings_obj.backup_repository)
    settings_obj.intended_repositories.add(settings_obj.intended_repository)


class Migration(migrations.Migration):

    dependencies = [
        ("nautobot_golden_config", "0006_multiple_repo_support"),
    ]

    operations = [
        migrations.RunPython(convert_many_repos),
    ]
