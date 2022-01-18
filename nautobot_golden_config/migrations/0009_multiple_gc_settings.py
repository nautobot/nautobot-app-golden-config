# Generated by Django 3.1.14 on 2022-02-04 09:52

from django.db import migrations, models
import django.db.models.deletion


def repo_convert_check_eligibility(apps, schema_editor):
    """
    Check if migration is applicable. Fail in case of many repositories created.
    """
    GoldenConfigSetting = apps.get_model("nautobot_golden_config", "GoldenConfigSetting")

    settings_obj = GoldenConfigSetting.objects.first()

    if settings_obj.backup_repository.all().count() > 1 or settings_obj.intended_repository.all().count() > 1:
        raise ValueError("Please manually remove multiple repositories from Golden Config Settings before applying this migration")


def convert_many_repos_part1(apps, schema_editor):
    """
    Add the current `backup_repository` and `intended_repository` objects values
    to the `FK` additional intermediary attritbute to retain data.`
    """
    GoldenConfigSetting = apps.get_model("nautobot_golden_config", "GoldenConfigSetting")

    settings_obj = GoldenConfigSetting.objects.first()

    if settings_obj.backup_repository:
        settings_obj.backup_repository_tmp = settings_obj.backup_repository.first()
        settings_obj.save()

    if settings_obj.intended_repository:
        settings_obj.intended_repository_tmp = settings_obj.intended_repository.first()
        settings_obj.save()


def convert_many_repos_part2(apps, schema_editor):
    """
    Add the current `backup_repository_tmp` and `intended_repository_tmp` object values
    to the FKs final attritbutes to retain data.`
    """
    GoldenConfigSetting = apps.get_model("nautobot_golden_config", "GoldenConfigSetting")

    settings_obj = GoldenConfigSetting.objects.first()

    if settings_obj.backup_repository_tmp:
        settings_obj.backup_repository = settings_obj.backup_repository_tmp
        settings_obj.save()

    if settings_obj.intended_repository_tmp:
        settings_obj.intended_repository = settings_obj.intended_repository_tmp
        settings_obj.save()


class Migration(migrations.Migration):

    dependencies = [
        ('extras', '0018_joblog_data_migration'),
        ('nautobot_golden_config', '0008_multi_repo_support_final'),
    ]

    operations = [
        migrations.RunPython(repo_convert_check_eligibility),

        migrations.AlterModelOptions(
            name='goldenconfigsetting',
            options={'ordering': ['-weight', 'name'], 'verbose_name': 'Golden Config Setting'},
        ),
        migrations.RemoveField(
            model_name='goldenconfigsetting',
            name='backup_match_rule',
        ),
        migrations.RemoveField(
            model_name='goldenconfigsetting',
            name='intended_match_rule',
        ),
        migrations.AddField(
            model_name='goldenconfigsetting',
            name='description',
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name='goldenconfigsetting',
            name='name',
            field=models.CharField(default='Default Settings', max_length=100, unique=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='goldenconfigsetting',
            name='slug',
            field=models.SlugField(default='default', max_length=100, unique=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='goldenconfigsetting',
            name='weight',
            field=models.PositiveSmallIntegerField(default=1000),
        ),
        migrations.AddField(
            model_name='goldenconfigsetting',
            name='backup_repository_tmp',
            field=models.ForeignKey(blank=True, limit_choices_to={'provided_contents__contains': 'nautobot_golden_config.backupconfigs'}, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='backup_repository', to='extras.gitrepository'),
        ),
        migrations.AddField(
            model_name='goldenconfigsetting',
            name='intended_repository_tmp',
            field=models.ForeignKey(blank=True, limit_choices_to={'provided_contents__contains': 'nautobot_golden_config.intendedconfigs'}, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='intended_repository', to='extras.gitrepository'),
        ),
        migrations.RunPython(convert_many_repos_part1),
        migrations.RemoveField(
            model_name='goldenconfigsetting',
            name='backup_repository',
        ),
        migrations.RemoveField(
            model_name='goldenconfigsetting',
            name='intended_repository',
        ),
        migrations.AddField(
            model_name='goldenconfigsetting',
            name='backup_repository',
            field=models.ForeignKey(blank=True, limit_choices_to={'provided_contents__contains': 'nautobot_golden_config.backupconfigs'}, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='backup_repository', to='extras.gitrepository'),
        ),
        migrations.AddField(
            model_name='goldenconfigsetting',
            name='intended_repository',
            field=models.ForeignKey(blank=True, limit_choices_to={'provided_contents__contains': 'nautobot_golden_config.intendedconfigs'}, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='intended_repository', to='extras.gitrepository'),
        ),
        migrations.RunPython(convert_many_repos_part2),
        migrations.RemoveField(
            model_name='goldenconfigsetting',
            name='backup_repository_tmp',
        ),
        migrations.RemoveField(
            model_name='goldenconfigsetting',
            name='intended_repository_tmp',
        ),
    ]
