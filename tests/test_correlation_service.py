from backend.services.correlation_service import calculate_correlation_risk_level


def test_calculate_low_correlation_risk():
    assert calculate_correlation_risk_level(0.4) == "low"


def test_calculate_medium_correlation_risk():
    assert calculate_correlation_risk_level(0.75) == "medium"


def test_calculate_high_correlation_risk():
    assert calculate_correlation_risk_level(0.95) == "high"


def test_calculate_negative_high_correlation_risk():
    assert calculate_correlation_risk_level(-0.95) == "high"