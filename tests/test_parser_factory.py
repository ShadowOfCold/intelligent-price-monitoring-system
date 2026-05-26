import pytest

from backend.parsers.parser_factory import get_parser
from backend.parsers.mvideo_parser import MVideoParser
from backend.parsers.citilink_parser import CitilinkParser
from backend.parsers.yandex_market_parser import YandexMarketParser


def test_get_mvideo_parser():
    assert isinstance(get_parser("М.Видео"), MVideoParser)


def test_get_citilink_parser():
    assert isinstance(get_parser("Ситилинк"), CitilinkParser)


def test_get_yandex_market_parser():
    assert isinstance(get_parser("Яндекс Маркет"), YandexMarketParser)


def test_get_unknown_parser():
    with pytest.raises(ValueError):
        get_parser("Неизвестный магазин")