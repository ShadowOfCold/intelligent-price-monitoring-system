from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database.dependencies import get_db
from backend.models.store import Store
from backend.schemas.store_schema import StoreCreate, StoreResponse

from urllib.parse import urlparse

def is_valid_url(value: str) -> bool:
    try:
        result = urlparse(value)
        return result.scheme in ("http", "https") and bool(result.netloc)
    except Exception:
        return False

router = APIRouter(prefix="/stores", tags=["Магазины"])

@router.post("/", response_model=StoreResponse)
def create_store(store_data: StoreCreate, db: Session = Depends(get_db)):
    existing_store = db.query(Store).filter(
        Store.name == store_data.name
    ).first()

    if existing_store is not None:
        raise HTTPException(
            status_code=400,
            detail="Магазин с таким названием уже существует"
        )
    
    if not is_valid_url(store_data.base_url):
        raise HTTPException(
            status_code=400,
            detail="Введите корректный адрес сайта"
        )

    store = Store(
        name=store_data.name,
        base_url=store_data.base_url
    )

    db.add(store)
    db.commit()
    db.refresh(store)

    return store


@router.get("/", response_model=list[StoreResponse])
def get_stores(db: Session = Depends(get_db)):
    return db.query(Store).order_by(Store.id).all()


@router.put("/{store_id}", response_model=StoreResponse)
def update_store(
    store_id: int,
    store_data: StoreCreate,
    db: Session = Depends(get_db)
):
    store = db.query(Store).filter(Store.id == store_id).first()

    if store is None:
        raise HTTPException(status_code=404, detail="Магазин не найден")

    existing_store = db.query(Store).filter(
        Store.name == store_data.name,
        Store.id != store_id
    ).first()

    if existing_store is not None:
        raise HTTPException(
            status_code=400,
            detail="Магазин с таким названием уже существует"
        )
    
    if not is_valid_url(store_data.base_url):
        raise HTTPException(
            status_code=400,
            detail="Введите корректный адрес сайта"
        )

    store.name = store_data.name
    store.base_url = store_data.base_url

    db.commit()
    db.refresh(store)

    return store


@router.delete("/{store_id}")
def delete_store(store_id: int, db: Session = Depends(get_db)):
    store = db.query(Store).filter(Store.id == store_id).first()

    if store is None:
        raise HTTPException(status_code=404, detail="Магазин не найден")

    db.delete(store)
    db.commit()

    return {"message": "Магазин успешно удалён"}