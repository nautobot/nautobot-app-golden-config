"""Add the run_config_compliance command to nautobot-server."""

from django.core.management.base import BaseCommand
from nautobot.extras.jobs import get_job

from nautobot_golden_config.utilities.management import job_runner


class Command(BaseCommand):
    """Boilerplate Command to inherit from BaseCommand."""

    help = "Run Config Compliance Job from Golden Config Plugin."

    def add_arguments(self, parser):
        """Add arguments for run_config_compliance."""
        parser.add_argument("-u", "--user", type=str, required=True, help="User to run the Job as.")
        parser.add_argument("-d", "--device", type=str, help="Define a uniquely defined device name")

    def handle(self, *args, **kwargs):
        """Add handler for run_config_compliance."""
        job_class = get_job("plugins/nautobot_golden_config.jobs/ComplianceJob")
        job_runner(self, job_class, kwargs.get("device"), kwargs.get("user"))
