from pydantic import BaseModel
from typing import List, Literal

class AlgorithmWeight(BaseModel):
    name: str
    percentage: float

class QualityCurveRequest(BaseModel):
    dataset_name: str
    target_dimension: Literal["2D", "3D"]
    mix_by: str
    algorithms: List[AlgorithmWeight]

class QualityCurveResponse(BaseModel):
    type: str = "quality_curve"
    curve: List[float]
    auc: float
    k_neighbors: int
    opt: str
