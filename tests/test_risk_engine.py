from core.risk_engine import risk_level_from_score


def test_risk_level_boundaries():
    assert risk_level_from_score(0) == "LOW"
    assert risk_level_from_score(30) == "MEDIUM"
    assert risk_level_from_score(60) == "HIGH"
    assert risk_level_from_score(85) == "CRITICAL"
    assert risk_level_from_score(100) == "CRITICAL"
