import backend.models

from fastapi import FastAPI

from backend.api.product_api import router as product_router
from backend.api.store_api import router as store_router
from backend.api.store_product_api import router as store_product_router
from backend.api.price_api import router as price_router
from backend.api.price_collection_api import router as price_collection_router
from backend.api.document_api import router as document_router

app = FastAPI(
    title="Интеллектуальная система мониторинга цен"
)

app.include_router(product_router)
app.include_router(store_router)
app.include_router(store_product_router)
app.include_router(price_router)
app.include_router(price_collection_router)
app.include_router(document_router)


@app.get("/")
def root():
    return {
        "message": "Интеллектуальная система мониторинга цен"
    }