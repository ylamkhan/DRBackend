from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Path
from starlette import status
import os, shutil

# Import your get_current_user dependency
from app.dependencies import get_current_user # Adjust this import path!
# from app.models.models import User # Optional: if you want type hinting for current_user

UPLOAD_FOLDER = "Datasets"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

router = APIRouter()

# ... (your existing /api/upload/, /api/list-files/, /api/delete-all-data/ endpoints) ...

@router.delete("/api/delete-file/{file_name}")
async def delete_single_file(
    file_name: str = Path(..., description="The name of the file to delete"),
    current_user: dict = Depends(get_current_user)
):
    """
    Deletes a specific file from the UPLOAD_FOLDER (Datasets).
    Requires authentication.
    """
    file_path = os.path.join(UPLOAD_FOLDER, file_name)

    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File '{file_name}' not found."
        )

    if not os.path.isfile(file_path):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"'{file_name}' is not a file."
        )

    try:
        os.remove(file_path)
        return {"message": f"File '{file_name}' deleted successfully."}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete file '{file_name}': {e}"
        )