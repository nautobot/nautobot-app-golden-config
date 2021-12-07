# -*- coding: utf-8 -*-
"""This file is meant to take the current ForeginKey relationship assosciated to
a single repository object from GoldenConfigSetting backup_repo and intended_repo
attribute and populate a temporary many_to_many attribute."""

from __future__ import unicode_literals

from django.db import models, migrations
from nautobot_golden_config.models import GoldenConfigSetting


def convert_many_repos(apps, schema_editor):
    """
    Add the current `backup_repositories` and `intended_repositories` objects
    to the `many_to_many` updated fields backup/intended.`
    """
    settings_obj = GoldenConfigSetting.objects.first()

    settings_obj.backup_repository.add(settings_obj.backup_repositories.all())
    settings_obj.intended_repositoy.add(settings_obj.intended_repositories.all())


class Migration(migrations.Migration):

    dependencies = [
        ("nautobot_golden_config", "0008_backup_intended_to_many"),
    ]

    operations = [
        migrations.RunPython(convert_many_repos),
    ]
