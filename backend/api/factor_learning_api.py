from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database.dependencies import get_db
from backend.schemas.factor_learning_schema import (
    FactorLearningCategoryRequest,
    FactorWeightComparisonResponse,
    LearnedFactorWeightResponse,
)
from backend.services.factor_learning_service import (
    calculate_factor_importance_for_all_categories,
    calculate_factor_importance_for_category,
    get_factor_weight_comparison,
    get_learned_factor_weights,
    apply_learned_factor_weights_for_category,
    apply_learned_factor_weights_for_all_categories,
)


router = APIRouter(
    prefix="/factor-learning",
    tags=["Обучение весов факторов"]
)


@router.post("/calculate/category")
def calculate_category_factor_weights(
    data: FactorLearningCategoryRequest,
    db: Session = Depends(get_db)
):
    try:
        return calculate_factor_importance_for_category(
            db=db,
            category=data.category,
        )

    except Exception as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )


@router.post("/calculate/all")
def calculate_all_factor_weights(
    db: Session = Depends(get_db)
):
    try:
        return calculate_factor_importance_for_all_categories(
            db=db
        )

    except Exception as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )


@router.get(
    "/weights",
    response_model=list[LearnedFactorWeightResponse]
)
def read_learned_factor_weights(
    db: Session = Depends(get_db)
):
    return get_learned_factor_weights(
        db=db
    )


@router.get(
    "/weights/{category}",
    response_model=list[LearnedFactorWeightResponse]
)
def read_learned_factor_weights_for_category(
    category: str,
    db: Session = Depends(get_db)
):
    return get_learned_factor_weights(
        db=db,
        category=category
    )

@router.get(
    "/comparison",
    response_model=list[FactorWeightComparisonResponse]
)
def read_factor_weight_comparison(
    db: Session = Depends(get_db)
):
    return get_factor_weight_comparison(
        db=db
    )

@router.get(
    "/comparison/{category}",
    response_model=list[FactorWeightComparisonResponse]
)
def read_factor_weight_comparison_for_category(
    category: str,
    db: Session = Depends(get_db)
):
    return get_factor_weight_comparison(
        db=db,
        category=category
    )

@router.post("/apply/category")
def apply_category_learned_factor_weights(
    data: FactorLearningCategoryRequest,
    db: Session = Depends(get_db)
):
    try:
        return apply_learned_factor_weights_for_category(
            db=db,
            category=data.category,
        )

    except Exception as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )


@router.post("/apply/all")
def apply_all_learned_factor_weights(
    db: Session = Depends(get_db)
):
    try:
        return apply_learned_factor_weights_for_all_categories(
            db=db
        )

    except Exception as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )