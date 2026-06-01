from sqlalchemy.orm import Session

from backend.models.product import Product
from backend.models.store_product import StoreProduct

from backend.services.anomaly_service import detect_anomalies_for_product
from backend.services.correlation_service import analyze_correlations_for_product
from backend.services.forecast_service import generate_forecast_for_store_product
from backend.services.market_factor_service import ensure_actual_market_factors
from backend.services.price_collection_service import collect_price_for_store_product
from backend.services.report_service import generate_excel_report, generate_pdf_report


def get_store_product_label(store_product: StoreProduct) -> str:
    product_name = (
        store_product.product.name
        if store_product.product
        else f"Товар #{store_product.product_id}"
    )

    store_name = (
        store_product.store.name
        if store_product.store
        else f"Магазин #{store_product.store_id}"
    )

    return f"{product_name} — {store_name} (карточка #{store_product.id})"


def run_full_monitoring_cycle(
    db: Session,
    collect_prices: bool = True,
    detect_anomalies: bool = True,
    analyze_correlations: bool = True,
    generate_forecasts: bool = True,
    generate_reports: bool = True,
    forecast_days_count: int = 7,
    report_format: str = "both"
):
    products = db.query(Product).all()
    store_products = db.query(StoreProduct).all()

    results = {
        "products_total": len(products),
        "store_products_total": len(store_products),

        "market_factors_checked": False,
        "market_factors_updated": False,
        "market_factors_result": None,

        "prices_expected": len(store_products) if collect_prices else 0,
        "prices_collected": 0,

        "products_analyzed_for_anomalies": 0,
        "anomalies_detected": 0,

        "products_analyzed_for_correlations": 0,
        "correlations_built": 0,

        "store_products_analyzed_for_forecasts": 0,
        "products_with_forecasts": 0,
        "forecast_points_created": 0,

        "reports_created": 0,

        "errors": []
    }

    try:
        market_factors_status = ensure_actual_market_factors(db=db)

        results["market_factors_checked"] = True
        results["market_factors_updated"] = market_factors_status["updated"]
        results["market_factors_result"] = market_factors_status

    except Exception as error:
        db.rollback()

        results["errors"].append(
            f"Рыночные факторы: {str(error)}"
        )

    forecast_product_ids = set()

    if collect_prices:
        for store_product in store_products:
            try:
                collect_price_for_store_product(
                    db=db,
                    store_product_id=store_product.id
                )

                results["prices_collected"] += 1

            except Exception as error:
                db.rollback()

                results["errors"].append(
                    f"Сбор цен [{get_store_product_label(store_product)}]: {str(error)}"
                )

    if detect_anomalies:
        for product in products:
            try:
                anomalies = detect_anomalies_for_product(
                    db=db,
                    product_id=product.id
                )

                results["products_analyzed_for_anomalies"] += 1
                results["anomalies_detected"] += len(anomalies)

            except Exception as error:
                db.rollback()

                results["errors"].append(
                    f"Аномалии [{product.name}]: {str(error)}"
                )

    if analyze_correlations:
        for product in products:
            try:
                correlations = analyze_correlations_for_product(
                    db=db,
                    product_id=product.id
                )

                results["products_analyzed_for_correlations"] += 1
                results["correlations_built"] += len(correlations)

            except Exception as error:
                db.rollback()

                results["errors"].append(
                    f"Корреляции [{product.name}]: {str(error)}"
                )

    if generate_forecasts:
        for store_product in store_products:
            try:
                forecast_result = generate_forecast_for_store_product(
                    db=db,
                    store_product_id=store_product.id,
                    days_count=forecast_days_count
                )

                created_forecasts_count = len(
                    forecast_result["forecasts"]
                )

                results["store_products_analyzed_for_forecasts"] += 1
                results["forecast_points_created"] += created_forecasts_count
                forecast_product_ids.add(store_product.product_id)

            except Exception as error:
                db.rollback()

                results["errors"].append(
                    f"Прогноз [{get_store_product_label(store_product)}]: {str(error)}"
                )

        results["products_with_forecasts"] = len(forecast_product_ids)

    if generate_reports:
        for product in products:
            try:
                if report_format in ("excel", "both"):
                    generate_excel_report(
                        db=db,
                        product_id=product.id
                    )

                    results["reports_created"] += 1

                if report_format in ("pdf", "both"):
                    generate_pdf_report(
                        db=db,
                        product_id=product.id
                    )

                    results["reports_created"] += 1

            except Exception as error:
                db.rollback()

                results["errors"].append(
                    f"Отчёты [{product.name}]: {str(error)}"
                )

    return results