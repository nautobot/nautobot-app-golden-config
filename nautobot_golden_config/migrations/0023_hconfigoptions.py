# Generated by Django 3.2.15 on 2023-04-21 23:00

import django.core.serializers.json
from django.db import migrations, models
import nautobot.extras.models.mixins
import taggit.managers
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('extras', '0047_enforce_custom_field_slug'),
        ('nautobot_golden_config', '0022_goldenconfig_remediation'),
    ]

    operations = [
        migrations.CreateModel(
            name='HConfigOptions',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('created', models.DateField(auto_now_add=True, null=True)),
                ('last_updated', models.DateTimeField(auto_now=True, null=True)),
                ('_custom_field_data', models.JSONField(blank=True, default=dict, encoder=django.core.serializers.json.DjangoJSONEncoder)),
                ('name', models.CharField(max_length=255)),
                ('hier_options', models.JSONField(default={})),
                ('tags', taggit.managers.TaggableManager(through='extras.TaggedItem', to='extras.Tag')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, nautobot.extras.models.mixins.DynamicGroupMixin, nautobot.extras.models.mixins.NotesMixin),
        ),
    ]
