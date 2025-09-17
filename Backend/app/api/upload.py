from fastapi import APIRouter, UploadFile, File, HTTPException,Depends
import os, shutil
from app.dependencies import get_current_user

UPLOAD_FOLDER = "Datasets"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

router = APIRouter()

@router.post("/api/upload/")
async def upload_file(
    file: UploadFile = File(...),
    # Add the dependency here to protect the endpoint
    current_user: dict = Depends(get_current_user) # Or User if you imported it
):
    """
    Uploads a file to the UPLOAD_FOLDER.
    Requires authentication.
    Raises an HTTPException if the file already exists.
    """
    print(f"User {current_user.email} is uploading a file.") # Debugging: See who is logged in

    file_location = os.path.join(UPLOAD_FOLDER, file.filename)
    # Check if file already exists
    if os.path.exists(file_location):
        raise HTTPException(
            status_code=409, detail=f"File '{file.filename}' already exists."
        )

    try:
        with open(file_location, "wb") as f:
            shutil.copyfileobj(file.file, f)
        return {"message": f"File '{file.filename}' uploaded successfully."}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to upload file: {e}"
        )
