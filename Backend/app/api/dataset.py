from fastapi import APIRouter, Depends, HTTPException
from app.dependencies import get_current_user
from app.services.dataset_store import Dataset
from app.api.cache import datasets_cache
import pandas as pd
import os
import asyncio
import contextlib
from app.api.websocket import safe_notify_clients_projection_ready

router = APIRouter()

DATASET_FOLDER = "Datasets"
current_dataset_filename = None  # Tracks currently loaded dataset filename
dataset_tasks = {}  # Tracks running async projection tasks


@router.get("/dataset/{namefile:path}")
async def get_dataset(namefile: str, current_user=Depends(get_current_user)):
    global current_dataset_filename

    # Normalize and secure the filename
    filename = os.path.basename(namefile)
    if not filename.endswith(".csv"):
        filename += ".csv"
    file_path = os.path.join(DATASET_FOLDER, filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"File '{filename}' not found")

    # Cancel previous dataset processing if switching to a new one
    if current_dataset_filename and current_dataset_filename != filename:
        old_dataset = datasets_cache.get(current_dataset_filename)
        if old_dataset:
            old_dataset.cancel() # Set the cancel flag
            print(f"Cancelling computation for {current_dataset_filename}")

        if current_dataset_filename in dataset_tasks:
            task = dataset_tasks.pop(current_dataset_filename)
            # Await the cancellation to ensure the old task finishes its cleanup
            # and doesn't interfere with the new one. Use suppress for robustness.
            with contextlib.suppress(asyncio.CancelledError):
                if not task.done(): # Only await if still running
                    task.cancel()
                    await task
            print(f"Cleaned up task for {current_dataset_filename}")
        
        # Important: Remove the old dataset from cache only AFTER its task is handled
        # This prevents a brief period where the old dataset might be accessed but its task is gone
        if current_dataset_filename in datasets_cache:
            del datasets_cache[current_dataset_filename]
            print(f"Removed {current_dataset_filename} from cache")


    # Use cached dataset if available
    if filename in datasets_cache:
        dataset = datasets_cache[filename]
        current_dataset_filename = filename  # Ensure tracking is consistent

        # If projections are ready, return them.
        if dataset.ready:
            return {
                "X": dataset.X.tolist(),
                "y": dataset.y,
                "projections": dataset.projections, # Return actual projections here
                "status": "ready"
            }
        else:
            # If not ready, indicate processing status but don't return incomplete projections
            return {
                "X": dataset.X.tolist(),
                "y": dataset.y,
                "projections": {"status": "processing"} # No actual data here yet
            }

    # Load and validate the CSV if not in cache
    try:
        df = pd.read_csv(file_path)

        required_columns = {"X", "Y", "Z", "Label"}
        if not required_columns.issubset(df.columns):
            raise HTTPException(status_code=400, detail="CSV must contain X, Y, Z, and Label columns")

        X = df[["X", "Y", "Z"]].values.tolist()
        y = df["Label"].tolist()

        dataset = Dataset(name=filename, X=X, y=y, defer_computation=True)
        datasets_cache[filename] = dataset
        current_dataset_filename = filename

        # Start async task for projections
        task = asyncio.create_task(dataset.compute_projections())
        dataset_tasks[filename] = task

        # Return initial status
        return {
            "X": dataset.X.tolist(),
            "y": dataset.y,
            "projections": {"status": "processing"} # Only status, no data yet
        }

    except Exception as e:
        # Clean up if an error occurs during initial loading
        if filename in datasets_cache:
            del datasets_cache[filename]
        if filename in dataset_tasks:
            task = dataset_tasks.pop(filename)
            with contextlib.suppress(asyncio.CancelledError):
                if not task.done():
                    task.cancel()
                    await task
        raise HTTPException(status_code=500, detail=f"Error processing dataset: {str(e)}")

# Add a new endpoint to specifically fetch projections when they are ready
@router.get("/dataset/{namefile:path}/projections")
async def get_dataset_projections(namefile: str, current_user=Depends(get_current_user)):
    filename = os.path.basename(namefile)
    if not filename.endswith(".csv"):
        filename += ".csv"

    if filename not in datasets_cache:
        raise HTTPException(status_code=404, detail=f"Dataset '{filename}' not found in cache.")

    dataset = datasets_cache[filename]

    if not dataset.ready:
        raise HTTPException(status_code=202, detail="Projections are still being computed.") # 202 Accepted, still processing

    return {
        "status": "ready",
        "projections": dataset.projections
    }