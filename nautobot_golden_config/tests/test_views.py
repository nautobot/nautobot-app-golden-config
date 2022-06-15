from nautobot.dcim.models import Platform
from nautobot.utilities.testing import ViewTestCases

from nautobot_golden_config.models import ConfigReplace


class ConfigReplaceTestCase(ViewTestCases.PrimaryObjectViewTestCase):
    model = ConfigReplace

    @classmethod
    def setUpTestData(cls):

        platforms = (
            Platform.objects.create(name="Platform 1", slug="platform-1"),
            Platform.objects.create(name="Platform 2", slug="platform-2"),
            Platform.objects.create(name="Platform 3", slug="platform-3"),
        )

        ConfigReplace.objects.create(
            name="Config replace 1",
            platform=platforms[0],
            description="foo bar",
            regex=r"username(\S+)",
            replace="<redacted>",
        )
        ConfigReplace.objects.create(
            name="Config replace 2",
            platform=platforms[1],
            description="foo bar",
            regex=r"username(\S+)",
            replace="<redacted>",
        )
        ConfigReplace.objects.create(
            name="Config replace 3",
            platform=platforms[2],
            description="foo bar",
            regex=r"username(\S+)",
            replace="<redacted>",
        )

        #tags = cls.create_tags("Alpha", "Bravo", "Charlie")

        cls.form_data = {
            "name": "Config replace X",
            "platform": platforms[1].pk,
            "description": "A new config replace",
            "regex": "username(\S+)",
            "replace": "<redacted>",
            #"tags": [t.pk for t in tags],
        }

        cls.csv_data = (
            "name,platform,description,regex,replace",
            "Config replace 4,Platform 1,description 1,username(\S+),<redacted>",
            "Config replace 5,Platform 2,description 2,username(\S+),<redacted>",
            "Config replace 6,Platform 3,description 3,username(\S+),<redacted>",
        )

        cls.bulk_edit_data = {
            "platform": platforms[1].pk,
        }
