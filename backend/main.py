import backend.models

from fastapi import FastAPI

from backend.api.product_api import router as product_router
from backend.api.store_api import router as store_router
from backend.api.store_product_api import router as store_product_router
from backend.api.price_api import router as price_router
from backend.api.price_collection_api import router as price_collection_router
from backend.api.document_api import router as document_router
from backend.api.anomaly_api import router as anomaly_router
from backend.api.correlation_api import router as correlation_router
from backend.api.forecast_api import router as forecast_router
from backend.api.report_api import router as report_router
from backend.api.scheduler_api import router as scheduler_router
from backend.api.market_factor_api import router as market_factor_router
from backend.api.factor_learning_api import router as factor_learning_router
from backend.services.scheduler_runtime_service import (
    start_scheduler,
    stop_scheduler,
)

app = FastAPI(
    title="Интеллектуальная система мониторинга цен"
)

app.include_router(product_router)
app.include_router(store_router)
app.include_router(store_product_router)
app.include_router(price_router)
app.include_router(price_collection_router)
app.include_router(document_router)
app.include_router(anomaly_router)
app.include_router(correlation_router)
app.include_router(forecast_router)
app.include_router(report_router)
app.include_router(scheduler_router)
app.include_router(market_factor_router)
app.include_router(factor_learning_router)

@app.get("/")
def root():
    return {
        "message": "Интеллектуальная система мониторинга цен"
    }

@app.on_event("startup")
def on_startup():
    start_scheduler()


@app.on_event("shutdown")
def on_shutdown():
    stop_scheduler()