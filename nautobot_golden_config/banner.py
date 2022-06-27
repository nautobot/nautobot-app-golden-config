"""Banner for GoldenConfig list view."""
from nautobot.extras.choices import BannerClassChoices
from nautobot.extras.plugins import PluginBanner

from nautobot_golden_config.models import GoldenConfig


def banner(context, *args, **kwargs):  # pylint: disable=inconsistent-return-statements
    """Creates a WARNING banner IF OPTIMIZE_HOME is enabled."""
    if "table" in context and context["table"].Meta.model == GoldenConfig:
        content = (
            "<div>Optimize Golden Config Home setting is enabled.<br/>"
            "A device will <strong>ONLY</strong> appear <strong>IF</strong> a Golden Config "
            "Backup, Intended, <strong>OR</strong> Compliance job has been run against it.</div>"
        )
        return PluginBanner(content=content, banner_class=BannerClassChoices.CLASS_WARNING)
