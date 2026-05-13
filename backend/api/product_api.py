from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database.dependencies import get_db
from backend.models.product import Product
from backend.schemas.product_schema import ProductCreate, ProductResponse

router = APIRouter(prefix="/products", tags=["Товары"])


@router.post("/", response_model=ProductResponse)
def create_product(product_data: ProductCreate, db: Session = Depends(get_db)):
    existing_product = db.query(Product).filter(
        Product.name == product_data.name
    ).first()

    if existing_product is not None:
        raise HTTPException(
            status_code=400,
            detail="Товар с таким названием уже существует"
        )

    product = Product(
        name=product_data.name,
        category=product_data.category
    )

    db.add(product)
    db.commit()
    db.refresh(product)

    return product


@router.get("/", response_model=list[ProductResponse])
def get_products(db: Session = Depends(get_db)):
    return db.query(Product).order_by(Product.id).all()


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    product_data: ProductCreate,
    db: Session = Depends(get_db)
):
    product = db.query(Product).filter(Product.id == product_id).first()

    if product is None:
        raise HTTPException(status_code=404, detail="Товар не найден")

    existing_product = db.query(Product).filter(
        Product.name == product_data.name,
        Product.id != product_id
    ).first()

    if existing_product is not None:
        raise HTTPException(
            status_code=400,
            detail="Товар с таким названием уже существует"
        )

    product.name = product_data.name
    product.category = product_data.category

    db.commit()
    db.refresh(product)

    return product


@router.delete("/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()

    if product is None:
        raise HTTPException(status_code=404, detail="Товар не найден")

    db.delete(product)
    db.commit()

    return {"message": "Товар успешно удалён"}