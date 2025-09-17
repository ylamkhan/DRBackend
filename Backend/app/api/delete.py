from fastapi import APIRouter, UploadFile, File, HTTPException,Depends
import os, shutil
from app.dependencies import get_current_user

UPLOAD_FOLDER = "Datasets"
# Ensure the upload folder exists when the application starts
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

router = APIRouter()

@router.delete("/api/delete-all-data/")
async def delete_all_data(
    # Add the dependency here to protect the endpoint
    current_user: dict = Depends(get_current_user) # Or User if you imported it
):
    """
    Deletes all files and subdirectories within the UPLOAD_FOLDER.
    Requires authentication.
    This action is irreversible.
    """
    print(f"User {current_user.email} is deleting all data.") # Debugging: See who is logged in

    try:
        # Check if the folder exists to avoid errors on shutil.rmtree if it's already gone
        if os.path.exists(UPLOAD_FOLDER) and os.path.isdir(UPLOAD_FOLDER):
            # Remove the entire folder and its contents
            shutil.rmtree(UPLOAD_FOLDER)
            # Recreate the empty folder after deletion
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            return {"message": "All data in 'Datasets' folder deleted successfully."}
        else:
            # If the folder doesn't exist, consider it already "deleted" or empty
            return {"message": "No 'Datasets' folder found or it was already empty."}
    except OSError as e:
        # Catch OS-level errors (e.g., permissions, file in use)
        raise HTTPException(
            status_code=500, detail=f"Error deleting data: {e}"
        )
    except Exception as e:
        # Catch any other unexpected errors
        raise HTTPException(
            status_code=500, detail=f"An unexpected error occurred: {e}"
        )