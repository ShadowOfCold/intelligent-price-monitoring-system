from backend.services.document_service import normalize_price


def test_normalize_price_with_ruble_symbol():
    assert normalize_price("54 999 ₽") == 54999.0


def test_normalize_price_with_comma():
    assert normalize_price("12999,50") == 12999.50


def test_normalize_price_invalid_value():
    assert normalize_price("нет цены") is None