from datetime import datetime

import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sqlalchemy.orm import Session

from backend.models.learned_factor_weight import LearnedFactorWeight
from backend.models.market_factor import MarketFactor
from backend.models.price import Price
from backend.models.product import Product
from backend.utils.datetime_utils import get_current_datetime
from backend.models.category_factor_weight import CategoryFactorWeight


MIN_SAMPLES_FOR_LEARNING = 30

FACTOR_NAMES = [
    "usd_rate",
    "eur_rate",
    "oil_price",
    "inflation_rate",
    "electronics_index",
    "ai_demand_index",
]


def get_normalized_category(category: str | None) -> str:
    return category or "default"


def build_learning_dataframe(
    db: Session,
    category: str | None
) -> pd.DataFrame:
    normalized_category = get_normalized_category(category)

    query = (
        db.query(Price, Product)
        .join(Product, Price.product_id == Product.id)
    )

    if normalized_category == "default":
        query = query.filter(Product.category.is_(None))
    else:
        query = query.filter(Product.category == normalized_category)

    price_rows = query.order_by(Price.checked_at).all()

    if not price_rows:
        return pd.DataFrame()

    rows = []

    for price, product in price_rows:
        row_date = price.checked_at.date()

        row = {
            "date": row_date,
            "price": float(price.price),
        }

        for factor_name in FACTOR_NAMES:
            factor = (
                db.query(MarketFactor)
                .filter(
                    MarketFactor.factor_name == factor_name,
                    MarketFactor.measured_at <= datetime.combine(
                        row_date,
                        datetime.max.time()
                    ),
                )
                .order_by(MarketFactor.measured_at.desc())
                .first()
            )

            if factor is None:
                row[factor_name] = None
            else:
                row[factor_name] = float(factor.value)

        rows.append(row)

    dataframe = pd.DataFrame(rows)

    dataframe = dataframe.dropna(
        subset=FACTOR_NAMES + ["price"]
    )

    return dataframe

def serialize_learned_factor_weight(item: LearnedFactorWeight) -> dict:
    return {
        "id": item.id,
        "category": item.category,
        "factor_name": item.factor_name,
        "importance": item.importance,
        "sample_size": item.sample_size,
        "calculated_at": item.calculated_at,
    }

def calculate_factor_importance_for_category(
    db: Session,
    category: str | None
) -> dict:
    normalized_category = get_normalized_category(category)

    dataframe = build_learning_dataframe(
        db=db,
        category=category
    )

    if len(dataframe) < MIN_SAMPLES_FOR_LEARNING:
        return {
            "category": normalized_category,
            "calculated": False,
            "reason": (
                f"Недостаточно данных для обучения. "
                f"Нужно минимум {MIN_SAMPLES_FOR_LEARNING}, сейчас {len(dataframe)}"
            ),
            "sample_size": len(dataframe),
            "items": [
                serialize_learned_factor_weight(item)
                for item in created_items
            ],
        }

    x = dataframe[FACTOR_NAMES]
    y = dataframe["price"]

    model = RandomForestRegressor(
        n_estimators=200,
        random_state=42
    )

    model.fit(x, y)

    importances = model.feature_importances_

    db.query(LearnedFactorWeight).filter(
        LearnedFactorWeight.category == normalized_category
    ).delete(synchronize_session=False)

    calculated_at = get_current_datetime()
    created_items = []

    for factor_name, importance in zip(FACTOR_NAMES, importances):
        item = LearnedFactorWeight(
            category=normalized_category,
            factor_name=factor_name,
            importance=float(importance),
            sample_size=len(dataframe),
            calculated_at=calculated_at,
        )

        db.add(item)
        created_items.append(item)

    db.commit()

    for item in created_items:
        db.refresh(item)

    return {
        "category": normalized_category,
        "calculated": True,
        "sample_size": len(dataframe),
        "items": created_items,
    }


def get_available_categories(db: Session) -> list[str | None]:
    categories = (
        db.query(Product.category)
        .distinct()
        .all()
    )

    result = []

    for category_tuple in categories:
        result.append(category_tuple[0])

    return result


def calculate_factor_importance_for_all_categories(db: Session) -> dict:
    categories = get_available_categories(db=db)

    results = []

    for category in categories:
        result = calculate_factor_importance_for_category(
            db=db,
            category=category
        )

        results.append(result)

    return {
        "count": len(results),
        "results": results,
    }


def get_learned_factor_weights(
    db: Session,
    category: str | None = None
) -> list[LearnedFactorWeight]:
    query = db.query(LearnedFactorWeight)

    if category is not None:
        query = query.filter(
            LearnedFactorWeight.category == get_normalized_category(category)
        )

    return (
        query
        .order_by(
            LearnedFactorWeight.category,
            LearnedFactorWeight.importance.desc()
        )
        .all()
    )

def get_factor_weight_comparison(
    db: Session,
    category: str | None = None
) -> list[dict]:
    query = db.query(CategoryFactorWeight)

    if category is not None:
        query = query.filter(
            CategoryFactorWeight.category == get_normalized_category(category)
        )

    expert_weights = query.all()

    result = []

    for expert_weight in expert_weights:
        learned_weight = (
            db.query(LearnedFactorWeight)
            .filter(
                LearnedFactorWeight.category == expert_weight.category,
                LearnedFactorWeight.factor_name == expert_weight.factor_name,
            )
            .order_by(LearnedFactorWeight.calculated_at.desc())
            .first()
        )

        learned_importance = None
        difference = None
        sample_size = None
        calculated_at = None

        if learned_weight is not None:
            learned_importance = learned_weight.importance
            difference = learned_weight.importance - expert_weight.weight
            sample_size = learned_weight.sample_size
            calculated_at = learned_weight.calculated_at

        result.append(
            {
                "category": expert_weight.category,
                "factor_name": expert_weight.factor_name,
                "expert_weight": expert_weight.weight,
                "learned_importance": learned_importance,
                "difference": difference,
                "sample_size": sample_size,
                "calculated_at": calculated_at,
            }
        )

    return sorted(
        result,
        key=lambda item: (
            item["category"],
            item["factor_name"]
        )
    )

def apply_learned_factor_weights_for_category(
    db: Session,
    category: str | None
) -> dict:
    normalized_category = get_normalized_category(category)

    if normalized_category == "default":
        return {
            "applied": False,
            "category": "default",
            "message": (
                "Обученные веса для default-категории не применяются. "
                "Default используется только как резервная модель для товаров без категории."
            ),
            "updated_count": 0
        }

    learned_weights = (
        db.query(LearnedFactorWeight)
        .filter(LearnedFactorWeight.category == normalized_category)
        .all()
    )

    if not learned_weights:
        return {
            "applied": False,
            "category": normalized_category,
            "message": "Для выбранной категории нет обученных весов",
            "updated_count": 0
        }

    updated_count = 0

    for learned_weight in learned_weights:
        expert_weight = (
            db.query(CategoryFactorWeight)
            .filter(
                CategoryFactorWeight.category == normalized_category,
                CategoryFactorWeight.factor_name == learned_weight.factor_name,
            )
            .first()
        )

        if expert_weight is None:
            expert_weight = CategoryFactorWeight(
                category=normalized_category,
                factor_name=learned_weight.factor_name,
                weight=learned_weight.importance
            )

            db.add(expert_weight)
        else:
            expert_weight.weight = learned_weight.importance

        updated_count += 1

    db.commit()

    return {
        "applied": True,
        "category": normalized_category,
        "message": "Обученные веса факторов применены",
        "updated_count": updated_count
    }


def apply_learned_factor_weights_for_all_categories(
    db: Session
) -> dict:
    categories = (
        db.query(LearnedFactorWeight.category)
        .distinct()
        .all()
    )

    results = []

    for category_tuple in categories:
        result = apply_learned_factor_weights_for_category(
            db=db,
            category=category_tuple[0]
        )

        results.append(result)

    return {
        "count": len(results),
        "results": results
    }