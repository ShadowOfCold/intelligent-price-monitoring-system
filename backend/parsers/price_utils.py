import re


def clean_price(price_text: str) -> float:
    if price_text is None:
        raise ValueError("Пустое значение цены")

    cleaned = re.sub(r"[^\d,.]", "", str(price_text))

    if not cleaned:
        raise ValueError("Не удалось извлечь цену из текста")

    cleaned = cleaned.replace(",", ".")

    if cleaned.count(".") > 1:
        parts = cleaned.split(".")
        cleaned = "".join(parts[:-1]) + "." + parts[-1]

    return float(cleaned)