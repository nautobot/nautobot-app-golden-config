# Code Reference

## Package directory structure

```
nautobot_golden_config/
├── __init__.py
├── api                             # Something about this folder
│   ├── __init__.py
│   ├── serializers.py
│   ├── urls.py
│   └── views.py
├── choices.py                      # What's in here
├── datasources.py                  # Etc
├── filters.py                      # Etc
├── forms.py
├── jobs.py
├── management
│   └── commands
├── migrations
├── models.py
├── navigation.py
├── nornir_plays
│   ├── config_backup.py
│   ├── config_compliance.py
│   ├── config_intended.py
│   └── processor.py
├── static
│   └── nautobot_golden_config
├── tables.py
├── template_content.py
├── templates
│   └── nautobot_golden_config
├── tests
│   ├── __init__.py
│   ├── conftest.py
│   ├── forms
│   ├── jinja_filters.py
│   ├── test_api.py
│   ├── test_datasources.py
│   ├── test_filters.py
│   ├── test_graphql.py
│   ├── test_models.py
│   ├── test_nornir_plays
│   └── test_utilities
├── urls.py
├── utilities
│   ├── __init__.py
│   ├── constant.py
│   ├── git.py
│   ├── graphql.py
│   ├── helper.py
│   ├── management.py
│   └── utils.py
└── views.py
```
