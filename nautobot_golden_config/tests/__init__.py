"""Unit tests for nautobot_golden_config plugin."""


def custom_compliance_func(obj):
    """Custom compliance testing"""

    # if obj.rule == 'foo' and obj.device.platform.slug == 'platform-1':
    actual_config = obj.actual
    compliance_int = 0
    compliance = False
    ordered = False
    missing = "No secret found"
    extra = ""
    for line in actual_config.splitlines():
        if line.strip().startswith("password"):
            compliance_int = 1
            compliance = True
            ordered = True
            missing = ""
            extra = ""
    return {
        "compliance": compliance,
        "compliance_int": compliance_int,
        "ordered": ordered,
        "missing": missing,
        "extra": extra,
    }
