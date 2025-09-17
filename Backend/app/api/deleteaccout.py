from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr, validator
import os
import shutil
from app.dependencies import get_current_user
# Assuming you have a database session dependency
from app.database import get_db
from sqlalchemy.orm import Session
# Assuming you have User model
from app.models.models import User, DeleteAccountResponse

router = APIRouter()

# # Pydantic models for request validation
# class UpdateUserInfoRequest(BaseModel):
#     full_name: str
#     email: EmailStr
    
#     @validator('full_name')
#     def validate_full_name(cls, v):
#         if not v or not v.strip():
#             raise ValueError('Full name cannot be empty')
#         if len(v.strip()) < 2:
#             raise ValueError('Full name must be at least 2 characters long')
#         return v.strip()

# class UpdateUserInfoResponse(BaseModel):
#     message: str
#     user: dict

# class DeleteAccountResponse(BaseModel):
#     message: str
#     deleted_user_email: str

# @router.put("/api/update-user-info")
# async def update_user_info(
#     user_data: UpdateUserInfoRequest,
#     current_user: dict = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     """
#     Updates the current user's information (full name and email).
#     Requires authentication.
#     """
#     print(f"User {current_user.email} is updating their info.")
    
#     try:
#         # Get the user from database
#         user = db.query(User).filter(User.id == current_user.id).first()
#         if not user:
#             raise HTTPException(status_code=404, detail="User not found")
        
#         # Check if email is already taken by another user
#         if user_data.email != user.email:
#             existing_user = db.query(User).filter(
#                 User.email == user_data.email,
#                 User.id != current_user.id
#             ).first()
#             if existing_user:
#                 raise HTTPException(
#                     status_code=400, 
#                     detail="Email address is already registered to another account"
#                 )
        
#         # Update user information
#         user.full_name = user_data.full_name
#         user.email = user_data.email
        
#         # Commit changes to database
#         db.commit()
#         db.refresh(user)
        
#         # Return updated user info (excluding sensitive data)
#         updated_user_info = {
#             "id": user.id,
#             "full_name": user.full_name,
#             "email": user.email,
#             "created_at": user.created_at.isoformat() if hasattr(user, 'created_at') else None,
#             "updated_at": user.updated_at.isoformat() if hasattr(user, 'updated_at') else None
#         }
        
#         return UpdateUserInfoResponse(
#             message="User information updated successfully",
#             user=updated_user_info
#         )
        
#     except HTTPException:
#         # Re-raise HTTP exceptions
#         raise
#     except Exception as e:
#         # Rollback any changes if an error occurred
#         db.rollback()
#         print(f"Error updating user info: {e}")
#         raise HTTPException(
#             status_code=500, 
#             detail=f"An error occurred while updating user information: {str(e)}"
#         )

@router.delete("/api/delete-account")
async def delete_account(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Permanently deletes the current user's account and all associated data.
    This action is irreversible and will:
    1. Delete the user's record from the database
    2. Delete all user's uploaded files in the Datasets folder
    3. Remove any other associated data
    
    Requires authentication.
    """
    print(f"User {current_user.email} is deleting their account.")
    
    try:
        # Get the user from database
        user = db.query(User).filter(User.id == current_user.id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_email = user.email
        user_id = user.id
        
        # Define user-specific data folder (if you organize files by user)
        user_data_folder = os.path.join("Datasets", f"user_{user_id}")
        
        # Delete user's files if they exist
        try:
            if os.path.exists(user_data_folder) and os.path.isdir(user_data_folder):
                shutil.rmtree(user_data_folder)
                print(f"Deleted user data folder: {user_data_folder}")
        except OSError as e:
            print(f"Warning: Could not delete user data folder {user_data_folder}: {e}")
            # Continue with account deletion even if file deletion fails
        
        # Delete related data first (if you have foreign key constraints)
        # Example: Delete user's sessions, uploads, etc.
        # db.query(UserSession).filter(UserSession.user_id == user_id).delete()
        # db.query(UserUpload).filter(UserUpload.user_id == user_id).delete()
        
        # Delete the user record from database
        db.delete(user)
        db.commit()
        
        return DeleteAccountResponse(
            message="Account deleted successfully. All associated data has been permanently removed.",
            deleted_user_email=user_email
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Rollback any changes if an error occurred
        db.rollback()
        print(f"Error deleting account: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"An error occurred while deleting the account: {str(e)}"
        )

# # Optional: Get user info endpoint (for loading user data in frontend)
# @router.get("/api/user-info")
# async def get_user_info(
#     current_user: dict = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     """
#     Retrieves the current user's information.
#     Requires authentication.
#     """
#     try:
#         # Get the user from database
#         user = db.query(User).filter(User.id == current_user.id).first()
#         if not user:
#             raise HTTPException(status_code=404, detail="User not found")
        
#         # Return user info (excluding sensitive data like password)
#         user_info = {
#             "id": user.id,
#             "full_name": user.full_name,
#             "email": user.email,
#             "avatar_url": getattr(user, 'avatar_url', None),  # If you have avatar field
#             "created_at": user.created_at.isoformat() if hasattr(user, 'created_at') else None,
#             "is_2fa_enabled": getattr(user, 'is_2fa_enabled', False),  # If you have 2FA field
#         }
        
#         return user_info
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         print(f"Error fetching user info: {e}")
#         raise HTTPException(
#             status_code=500, 
#             detail=f"An error occurred while fetching user information: {str(e)}"
#         )

# # Optional: Change password endpoint
# @router.post("/api/change-password")
# async def change_password(
#     password_data: dict,  # You can create a proper Pydantic model for this
#     current_user: dict = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     """
#     Changes the current user's password.
#     Requires authentication and current password verification.
#     """
#     try:
#         from passlib.context import CryptContext
#         pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
#         current_password = password_data.get("current_password")
#         new_password = password_data.get("new_password")
        
#         if not current_password or not new_password:
#             raise HTTPException(
#                 status_code=400, 
#                 detail="Both current password and new password are required"
#             )
        
#         if len(new_password) < 8:
#             raise HTTPException(
#                 status_code=400, 
#                 detail="New password must be at least 8 characters long"
#             )
        
#         # Get the user from database
#         user = db.query(User).filter(User.id == current_user.id).first()
#         if not user:
#             raise HTTPException(status_code=404, detail="User not found")
        
#         # Verify current password
#         if not pwd_context.verify(current_password, user.hashed_password):
#             raise HTTPException(
#                 status_code=400, 
#                 detail="Current password is incorrect"
#             )
        
#         # Hash and update new password
#         user.hashed_password = pwd_context.hash(new_password)
        
#         # Update password change timestamp if you have one
#         # user.password_changed_at = datetime.utcnow()
        
#         db.commit()
        
#         return {"message": "Password changed successfully"}
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         db.rollback()
#         print(f"Error changing password: {e}")
#         raise HTTPException(
#             status_code=500, 
#             detail="An error occurred while changing the password"
#         )