from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from app.dependencies import get_current_user
from app.services.dataset_store import Dataset
import pandas as pd
import os
from app.api.cache import datasets_cache

router = APIRouter()
DATASET_FOLDER = "Datasets"

@router.get("/dataset/status/{namefile:path}")
def get_dataset_status(namefile: str, current_user=Depends(get_current_user)):
    filename = os.path.basename(namefile)
    if not filename.endswith(".csv"):
        filename += ".csv"
    print(filename)

    dataset = datasets_cache.get(filename)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not loaded yet")

    return {"ready": dataset.ready}