from backend.services.anomaly_service import calculate_risk_level


def test_calculate_low_risk_level():
    assert calculate_risk_level(0.2) == "low"


def test_calculate_medium_risk_level():
    assert calculate_risk_level(0.5) == "medium"


def test_calculate_high_risk_level():
    assert calculate_risk_level(0.8) == "high"