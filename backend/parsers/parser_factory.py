from backend.parsers.citilink_parser import CitilinkParser
from backend.parsers.mvideo_parser import MVideoParser
from backend.parsers.yandex_market_parser import YandexMarketParser


def get_parser(store_name: str):
    normalized_name = store_name.lower().strip()

    if (
        "мвидео" in normalized_name
        or "м.видео" in normalized_name
        or "mvideo" in normalized_name
        or "m.video" in normalized_name
    ):
        return MVideoParser()

    if (
        "ситилинк" in normalized_name
        or "citilink" in normalized_name
    ):
        return CitilinkParser()

    if (
        "яндекс" in normalized_name
        or "маркет" in normalized_name
        or "yandex" in normalized_name
        or "market" in normalized_name
    ):
        return YandexMarketParser()

    raise ValueError(
        f"Парсер для магазина '{store_name}' не реализован"
    )