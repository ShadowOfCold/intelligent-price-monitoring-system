import pytest

from backend.parsers.price_utils import clean_price


def test_clean_price_with_ruble_symbol():
    assert clean_price("54 999 ₽") == 54999.0


def test_clean_price_with_non_breaking_space():
    assert clean_price("31\u00a0350 ₽") == 31350.0


def test_clean_price_with_comma():
    assert clean_price("12999,50") == 12999.50


def test_clean_price_empty_value():
    with pytest.raises(ValueError):
        clean_price("")