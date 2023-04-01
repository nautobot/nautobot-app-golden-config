from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("extras", "0018_joblog_data_migration"),
        ("nautobot_golden_config", "0008_multi_repo_support_final"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="goldenconfigsetting",
            options={"ordering": ["-weight", "name"], "verbose_name": "Golden Config Setting"},
        ),
        migrations.RemoveField(
            model_name="goldenconfigsetting",
            name="backup_match_rule",
        ),
        migrations.RemoveField(
            model_name="goldenconfigsetting",
            name="intended_match_rule",
        ),
        migrations.AddField(
            model_name="goldenconfigsetting",
            name="description",
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name="goldenconfigsetting",
            name="name",
            field=models.CharField(default="Default Settings", max_length=100, unique=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="goldenconfigsetting",
            name="slug",
            field=models.SlugField(default="default", max_length=100, unique=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="goldenconfigsetting",
            name="weight",
            field=models.PositiveSmallIntegerField(default=1000),
        ),
        migrations.AddField(
            model_name="goldenconfigsetting",
            name="backup_repository_tmp",
            field=models.ForeignKey(
                blank=True,
                limit_choices_to={"provided_contents__contains": "nautobot_golden_config.backupconfigs"},
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="backup_repository",
                to="extras.gitrepository",
            ),
        ),
        migrations.AddField(
            model_name="goldenconfigsetting",
            name="intended_repository_tmp",
            field=models.ForeignKey(
                blank=True,
                limit_choices_to={"provided_contents__contains": "nautobot_golden_config.intendedconfigs"},
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="intended_repository",
                to="extras.gitrepository",
            ),
        ),
    ]
