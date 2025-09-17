# app/api/endpoints/quality.py
from fastapi import APIRouter, HTTPException
from app.schemas.quality import QualityCurveRequest, QualityCurveResponse
from app.api.cache import datasets_cache
from app.services.algorithm_utils import normalize_algorithm_name
from nxcurve import quality_curve
import numpy as np
import asyncio

router = APIRouter()

@router.post("/quality-curve", response_model=QualityCurveResponse)
async def compute_quality_curve(payload: QualityCurveRequest):
    dataset_key = payload.dataset_name + ".csv"

    if dataset_key not in datasets_cache:
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_key}' not found")

    dataset = datasets_cache[dataset_key]

    if not dataset.ready:
        raise HTTPException(status_code=400, detail="Dataset projections not ready yet")

    X = dataset.X
    n_components = 2 if payload.target_dimension == "2D" else 3
    dim_key = "2d" if n_components == 2 else "3d"
    mix_type = payload.mix_by.lower()

    if mix_type not in dataset.projections:
        raise HTTPException(status_code=400, detail=f"Mix type '{mix_type}' not found in projections")

    total = sum(algo.percentage for algo in payload.algorithms)
    if total != 100:
        raise HTTPException(status_code=400, detail="Percentages must sum to 100")

    blended = np.zeros((X.shape[0], n_components))
    for algo in payload.algorithms:
        try:
            proj = dataset.projections[mix_type][dim_key][algo.name]
        except KeyError:
            raise HTTPException(status_code=400, detail=f"Projection '{algo.name}' not available")
        blended += np.array(proj) * (algo.percentage / 100.0)

    try:
        nx_values, auc, _ = await asyncio.to_thread(
            quality_curve, X, blended, 20, "r", False
        )

        return QualityCurveResponse(
            curve=nx_values.tolist(),
            auc=float(auc),
            k_neighbors=20,
            opt="r"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RNX computation failed: {str(e)}")
