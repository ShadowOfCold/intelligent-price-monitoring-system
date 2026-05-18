from datetime import datetime
from itertools import combinations

import pandas as pd
from sqlalchemy.orm import Session

from backend.models.correlation_analysis_result import CorrelationAnalysisResult
from backend.models.price import Price
from backend.models.store import Store
from backend.models.store_product import StoreProduct
from backend.utils.datetime_utils import get_current_datetime

MIN_POINTS_FOR_CORRELATION = 3


def calculate_correlation_risk_level(correlation_value: float) -> str:
    abs_value = abs(correlation_value)

    if abs_value >= 0.9:
        return "high"

    if abs_value >= 0.7:
        return "medium"

    return "low"


def analyze_correlations_for_product(
    db: Session,
    product_id: int
) -> list[CorrelationAnalysisResult]:
    store_products = (
        db.query(StoreProduct)
        .filter(StoreProduct.product_id == product_id)
        .all()
    )

    if len(store_products) < 2:
        raise ValueError(
            "Для корреляционного анализа необходимо минимум две карточки товара"
        )

    db.query(CorrelationAnalysisResult).filter(
        CorrelationAnalysisResult.product_id == product_id
    ).delete(synchronize_session=False)

    results = []

    for first_store_product, second_store_product in combinations(store_products, 2):
        first_prices = (
            db.query(Price)
            .filter(Price.store_product_id == first_store_product.id)
            .order_by(Price.checked_at)
            .all()
        )

        second_prices = (
            db.query(Price)
            .filter(Price.store_product_id == second_store_product.id)
            .order_by(Price.checked_at)
            .all()
        )

        if (
            len(first_prices) < MIN_POINTS_FOR_CORRELATION
            or len(second_prices) < MIN_POINTS_FOR_CORRELATION
        ):
            continue

        first_df = pd.DataFrame(
            [
                {
                    "date": price.checked_at.date(),
                    "first_price": float(price.price)
                }
                for price in first_prices
            ]
        )

        second_df = pd.DataFrame(
            [
                {
                    "date": price.checked_at.date(),
                    "second_price": float(price.price)
                }
                for price in second_prices
            ]
        )

        first_df = first_df.groupby("date", as_index=False)["first_price"].mean()
        second_df = second_df.groupby("date", as_index=False)["second_price"].mean()

        merged_df = pd.merge(
            first_df,
            second_df,
            on="date",
            how="inner"
        )

        if len(merged_df) < MIN_POINTS_FOR_CORRELATION:
            continue

        correlation_value = merged_df["first_price"].corr(
            merged_df["second_price"]
        )

        if pd.isna(correlation_value):
            continue

        period_start = datetime.combine(
            merged_df["date"].min(),
            datetime.min.time()
        )

        period_end = datetime.combine(
            merged_df["date"].max(),
            datetime.max.time()
        )

        result = CorrelationAnalysisResult(
            product_id=product_id,
            first_store_product_id=first_store_product.id,
            second_store_product_id=second_store_product.id,
            correlation_value=float(correlation_value),
            period_start=period_start,
            period_end=period_end,
            risk_level=calculate_correlation_risk_level(correlation_value),
            created_at=get_current_datetime()
        )

        db.add(result)
        results.append(result)

    db.commit()

    for result in results:
        db.refresh(result)

    return results


def get_correlations_for_product(
    db: Session,
    product_id: int
):
    results = (
        db.query(CorrelationAnalysisResult)
        .filter(CorrelationAnalysisResult.product_id == product_id)
        .order_by(CorrelationAnalysisResult.created_at.desc())
        .all()
    )

    response = []

    for result in results:
        first_store_product = db.query(StoreProduct).filter(
            StoreProduct.id == result.first_store_product_id
        ).first()

        second_store_product = db.query(StoreProduct).filter(
            StoreProduct.id == result.second_store_product_id
        ).first()

        first_store = db.query(Store).filter(
            Store.id == first_store_product.store_id
        ).first()

        second_store = db.query(Store).filter(
            Store.id == second_store_product.store_id
        ).first()

        response.append(
            {
                "id": result.id,
                "product_id": result.product_id,
                "first_store_product_id": result.first_store_product_id,
                "second_store_product_id": result.second_store_product_id,
                "first_store_name": first_store.name,
                "second_store_name": second_store.name,
                "correlation_value": result.correlation_value,
                "period_start": result.period_start,
                "period_end": result.period_end,
                "risk_level": result.risk_level,
                "created_at": result.created_at,
            }
        )

    return response


def delete_correlations_for_product(
    db: Session,
    product_id: int
) -> int:
    deleted_count = (
        db.query(CorrelationAnalysisResult)
        .filter(CorrelationAnalysisResult.product_id == product_id)
        .delete(synchronize_session=False)
    )

    db.commit()

    return deleted_count