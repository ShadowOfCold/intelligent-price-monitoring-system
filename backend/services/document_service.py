import re
from datetime import datetime
from pathlib import Path

import pandas as pd
import pdfplumber
from sqlalchemy.orm import Session

from backend.models.price import Price
from backend.models.product import Product


DOCUMENTS_DIRECTORY = Path("data/raw/procurement_documents")


def normalize_price(value) -> float | None:
    try:
        cleaned = (
            str(value)
            .replace(" ", "")
            .replace("\xa0", "")
            .replace(",", ".")
        )

        cleaned = re.sub(r"[^\d.]", "", cleaned)

        if not cleaned:
            return None

        return float(cleaned)

    except Exception:
        return None


def get_or_create_product(db: Session, product_name: str) -> Product:
    product = db.query(Product).filter(
        Product.name.ilike(product_name)
    ).first()

    if product is not None:
        return product

    product = Product(
        name=product_name,
        category=None
    )

    db.add(product)
    db.commit()
    db.refresh(product)

    return product


def parse_procurement_excel(
    db: Session,
    file_path: str,
    document_id: int,
    price_checked_at: datetime
):
    dataframe = pd.read_excel(file_path)

    dataframe.columns = [
        str(column).strip().lower()
        for column in dataframe.columns
    ]

    product_column = None
    price_column = None

    possible_product_columns = [
        "товар",
        "наименование",
        "название",
        "product",
        "product_name",
    ]

    possible_price_columns = [
        "цена",
        "стоимость",
        "price",
    ]

    for column in dataframe.columns:
        if column in possible_product_columns:
            product_column = column

        if column in possible_price_columns:
            price_column = column

    if product_column is None:
        raise ValueError("В Excel-файле не найден столбец с товарами")

    if price_column is None:
        raise ValueError("В Excel-файле не найден столбец с ценами")

    added_prices = []

    for _, row in dataframe.iterrows():
        product_name = str(row[product_column]).strip()

        if not product_name or product_name.lower() == "nan":
            continue

        price_value = normalize_price(row[price_column])

        if price_value is None:
            continue

        product = get_or_create_product(
            db=db,
            product_name=product_name
        )

        price = Price(
            product_id=product.id,
            store_product_id=None,
            document_id=document_id,
            price=price_value,
            checked_at=price_checked_at
        )

        db.add(price)
        added_prices.append(price)

    db.commit()

    return added_prices


def parse_procurement_pdf(
    db: Session,
    file_path: str,
    document_id: int,
    price_checked_at: datetime
):
    with pdfplumber.open(file_path) as pdf:
        text_parts = []

        for page in pdf.pages:
            page_text = page.extract_text()

            if page_text:
                text_parts.append(page_text)

    full_text = "\n".join(text_parts)

    if not full_text.strip():
        raise ValueError("Не удалось извлечь текст из PDF-документа")

    added_prices = []

    for line in full_text.splitlines():
        line = line.strip()

        if not line:
            continue

        if "товар" in line.lower() and "цена" in line.lower():
            continue

        match = re.match(
            r"(.+?)\s+(\d[\d\s.,]*)\s*(?:₽|руб\.?)?$",
            line,
            re.IGNORECASE
        )

        if not match:
            continue

        product_name = match.group(1).strip()
        price_value = normalize_price(match.group(2))

        if not product_name or price_value is None:
            continue

        product = get_or_create_product(
            db=db,
            product_name=product_name
        )

        price = Price(
            product_id=product.id,
            store_product_id=None,
            document_id=document_id,
            price=price_value,
            checked_at=price_checked_at
        )

        db.add(price)
        added_prices.append(price)

    db.commit()

    if not added_prices:
        raise ValueError(
            "В PDF-документе не удалось найти строки формата: название товара и цена"
        )

    return added_prices


def parse_procurement_document(
    db: Session,
    file_path: str,
    file_type: str,
    document_id: int,
    price_checked_at: datetime
):
    if file_type in ["XLSX", "XLS"]:
        return parse_procurement_excel(
            db=db,
            file_path=file_path,
            document_id=document_id,
            price_checked_at=price_checked_at
        )

    if file_type == "PDF":
        return parse_procurement_pdf(
            db=db,
            file_path=file_path,
            document_id=document_id,
            price_checked_at=price_checked_at
        )

    raise ValueError("Неподдерживаемый тип документа")