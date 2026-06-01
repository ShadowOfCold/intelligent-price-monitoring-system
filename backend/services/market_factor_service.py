import xml.etree.ElementTree as ET
from datetime import datetime
from datetime import timedelta

import requests
import yfinance as yf
from sqlalchemy.orm import Session

from backend.models.category_factor_weight import CategoryFactorWeight
from backend.models.market_factor import MarketFactor

CBR_DAILY_URL = "https://www.cbr.ru/scripts/XML_daily.asp"

DEFAULT_FACTOR_WEIGHTS = [
    ("default", "usd_rate", 0.35),
    ("default", "eur_rate", 0.25),
    ("default", "oil_price", 0.25),
    ("default", "inflation_rate", 0.15),

    ("Электроника", "usd_rate", 0.35),
    ("Электроника", "eur_rate", 0.15),
    ("Электроника", "electronics_index", 0.30),
    ("Электроника", "ai_demand_index", 0.20),
]

FACTOR_ACTUALITY_HOURS = 12

def create_or_update_market_factor(
    db: Session,
    factor_name: str,
    factor_type: str,
    value: float,
    measured_at: datetime,
) -> MarketFactor:
    factor = (
        db.query(MarketFactor)
        .filter(
            MarketFactor.factor_name == factor_name,
            MarketFactor.measured_at == measured_at,
        )
        .first()
    )

    if factor is None:
        factor = MarketFactor(
            factor_name=factor_name,
            factor_type=factor_type,
            value=value,
            measured_at=measured_at,
        )
        db.add(factor)
    else:
        factor.factor_type = factor_type
        factor.value = value

    db.commit()
    db.refresh(factor)

    return factor


def get_market_factors(db: Session) -> list[MarketFactor]:
    return (
        db.query(MarketFactor)
        .order_by(
            MarketFactor.measured_at.desc(),
            MarketFactor.factor_name
        )
        .all()
    )


def get_market_factors_for_date(
    db: Session,
    target_date: datetime,
) -> dict[str, float]:
    target_day = target_date.date()

    factors = db.query(MarketFactor).all()

    result = {}

    for factor in factors:
        if factor.measured_at.date() <= target_day:
            current = result.get(factor.factor_name)

            if current is None:
                result[factor.factor_name] = factor

            elif factor.measured_at > current.measured_at:
                result[factor.factor_name] = factor

    return {
        factor_name: factor.value
        for factor_name, factor in result.items()
    }


def create_or_update_category_factor_weight(
    db: Session,
    category: str,
    factor_name: str,
    weight: float,
) -> CategoryFactorWeight:
    factor_weight = (
        db.query(CategoryFactorWeight)
        .filter(
            CategoryFactorWeight.category == category,
            CategoryFactorWeight.factor_name == factor_name,
        )
        .first()
    )

    if factor_weight is None:
        factor_weight = CategoryFactorWeight(
            category=category,
            factor_name=factor_name,
            weight=weight,
        )
        db.add(factor_weight)
    else:
        factor_weight.weight = weight

    db.commit()
    db.refresh(factor_weight)

    return factor_weight


def get_factor_weights_for_category(
    db: Session,
    category: str | None,
) -> list[CategoryFactorWeight]:
    normalized_category = category or "default"

    weights = (
        db.query(CategoryFactorWeight)
        .filter(CategoryFactorWeight.category == normalized_category)
        .order_by(CategoryFactorWeight.factor_name)
        .all()
    )

    if weights:
        return weights

    return (
        db.query(CategoryFactorWeight)
        .filter(CategoryFactorWeight.category == "default")
        .order_by(CategoryFactorWeight.factor_name)
        .all()
    )


def initialize_default_factor_weights(db: Session) -> dict:
    created_or_updated = []

    for category, factor_name, weight in DEFAULT_FACTOR_WEIGHTS:
        factor_weight = create_or_update_category_factor_weight(
            db=db,
            category=category,
            factor_name=factor_name,
            weight=weight,
        )

        created_or_updated.append(factor_weight)

    return {
        "count": len(created_or_updated),
        "items": created_or_updated,
    }


def update_currency_rates_from_cbr(db: Session) -> dict:
    now = datetime.now()
    today = datetime(
        year=now.year,
        month=now.month,
        day=now.day
    )
    date_req = today.strftime("%d/%m/%Y")

    response = requests.get(
        CBR_DAILY_URL,
        params={"date_req": date_req},
        timeout=30
    )
    response.raise_for_status()

    root = ET.fromstring(response.content)

    updated = []

    currency_map = {
        "USD": "usd_rate",
        "EUR": "eur_rate",
    }

    for valute in root.findall("Valute"):
        char_code = valute.findtext("CharCode")

        if char_code not in currency_map:
            continue

        value_text = valute.findtext("Value")

        if value_text is None:
            continue

        value = float(value_text.replace(",", "."))

        factor = create_or_update_market_factor(
            db=db,
            factor_name=currency_map[char_code],
            factor_type="currency",
            value=value,
            measured_at=today,
        )

        updated.append(factor)

    if len(updated) < 2:
        raise ValueError("ЦБ РФ не вернул курсы USD и EUR")

    return {
        "count": len(updated),
        "items": updated,
    }


def update_oil_price(db: Session) -> dict:
    try:
        ticker = yf.Ticker("CL=F")
        history = ticker.history(period="5d")

        if history.empty:
            raise ValueError("Yahoo Finance не вернул данные по нефти")

        latest_row = history.iloc[-1]
        oil_price = float(latest_row["Close"])
        raw_measured_at = history.index[-1].to_pydatetime()

        measured_at = datetime(
            year=raw_measured_at.year,
            month=raw_measured_at.month,
            day=raw_measured_at.day
        )

        factor = create_or_update_market_factor(
            db=db,
            factor_name="oil_price",
            factor_type="commodity",
            value=oil_price,
            measured_at=measured_at,
        )

        return {
            "count": 1,
            "items": [factor],
        }

    except Exception as error:
        raise ValueError(
            f"Ошибка получения цены нефти: {str(error)}"
        )


def update_market_factors_from_external_sources(db: Session) -> dict:
    result = {
        "updated": [],
        "errors": [],
    }

    try:
        currency_result = update_currency_rates_from_cbr(db=db)

        result["updated"].append(
            {
                "source": "cbr",
                "count": currency_result["count"],
            }
        )

    except Exception as error:
        db.rollback()

        result["errors"].append(
            f"ЦБ РФ: {str(error)}"
        )

    try:
        oil_result = update_oil_price(db=db)

        result["updated"].append(
            {
                "source": "yahoo_finance",
                "count": oil_result["count"],
            }
        )

    except Exception as error:
        db.rollback()

        result["errors"].append(
            f"Yahoo Finance: {str(error)}"
        )

    return result

def has_actual_market_factors(db: Session) -> bool:
    now = datetime.now()
    min_actual_datetime = now - timedelta(hours=FACTOR_ACTUALITY_HOURS)

    required_factors = [
        "usd_rate",
        "eur_rate",
        "oil_price",
    ]

    for factor_name in required_factors:
        factor = (
            db.query(MarketFactor)
            .filter(
                MarketFactor.factor_name == factor_name,
                MarketFactor.measured_at >= min_actual_datetime,
            )
            .order_by(MarketFactor.measured_at.desc())
            .first()
        )

        if factor is None:
            return False

    return True


def ensure_actual_market_factors(db: Session) -> dict:
    if has_actual_market_factors(db=db):
        return {
            "updated": False,
            "message": "Рыночные факторы актуальны",
            "result": None,
        }

    result = update_market_factors_from_external_sources(db=db)

    return {
        "updated": True,
        "message": "Рыночные факторы обновлены",
        "result": result,
    }