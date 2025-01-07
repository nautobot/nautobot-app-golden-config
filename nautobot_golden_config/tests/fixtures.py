"""Create fixtures for tests."""

from nautobot_golden_config.models import ComplianceFeature


def create_compliancefeature():
    """Fixture to create necessary number of ComplianceFeature for tests."""
    ComplianceFeature.objects.create(name="Test One")
    ComplianceFeature.objects.create(name="Test Two")
    ComplianceFeature.objects.create(name="Test Three")
