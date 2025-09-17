# app/routes/data.py

from fastapi import APIRouter, Depends
from app.dependencies import get_current_user
import os

router = APIRouter()
DATASET_FOLDER = "Datasets"

@router.get("/dataset/", response_model=list[str])
def get_dataset(current_user = Depends(get_current_user)):
    # Now only authenticated users can access this route
    if not os.path.exists(DATASET_FOLDER):
        return []
    
    files = [
        os.path.splitext(f)[0]
        for f in os.listdir(DATASET_FOLDER)
        if os.path.isfile(os.path.join(DATASET_FOLDER, f))
    ]
    return files
