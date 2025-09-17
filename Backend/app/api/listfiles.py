from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
import os, shutil

# Import your get_current_user dependency
from app.dependencies import get_current_user # Adjust this import path!
# from app.models.models import User # Optional: if you want type hinting for current_user

UPLOAD_FOLDER = "Datasets"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

router = APIRouter()

# ... (your existing /api/upload/ and /api/delete-all-data/ endpoints) ...

@router.get("/api/list-files/")
async def list_files(
    current_user: dict = Depends(get_current_user) # Protect this endpoint
):
    """
    Lists all files present in the UPLOAD_FOLDER (Datasets).
    Requires authentication.
    """
    files_list = []
    try:
        # Ensure the directory exists before trying to list its contents
        if os.path.exists(UPLOAD_FOLDER) and os.path.isdir(UPLOAD_FOLDER):
            for filename in os.listdir(UPLOAD_FOLDER):
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                if os.path.isfile(filepath): # Only list actual files, not subdirectories
                    file_size = os.path.getsize(filepath) # Size in bytes
                    files_list.append({
                        "name": filename,
                        "size": f"{file_size / 1024:.2f} KB" # Format size to KB
                    })
        # If folder doesn't exist, files_list remains empty, which is fine
        return {"files": files_list}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve file list: {e}"
        )