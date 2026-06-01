from datetime import datetime

from pydantic import BaseModel


class LearnedFactorWeightResponse(BaseModel):
    id: int
    category: str
    factor_name: str
    importance: float
    sample_size: int
    calculated_at: datetime

    class Config:
        from_attributes = True


class FactorLearningCategoryRequest(BaseModel):
    category: str | None = None

class FactorWeightComparisonResponse(BaseModel):
    category: str
    factor_name: str
    expert_weight: float
    learned_importance: float | None = None
    difference: float | None = None
    sample_size: int | None = None
    calculated_at: datetime | None = None