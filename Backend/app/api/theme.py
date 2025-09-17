from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer
# Import TokenRefreshRequest
from app.models.models import User, UpdateUserInfoRequest, UpdateUserInfoResponse, ThemeUpdate
from app.database import get_db
from app.dependencies import get_current_user
from app.security.token_blacklist import blacklist_manager
from jose import JWTError # Import JWTError for token decoding errors



router = APIRouter()

@router.put("/update-theme")
async def update_theme(
    theme: ThemeUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Updates the current user's information (full name and email).
    Requires authentication.
    """
    print(f"User {current_user.email} is updating their info.")
    
    try:
        # Get the user from database
        user = db.query(User).filter(User.id == current_user.id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Update user information
        user.theme = theme.theme
        
        # Commit changes to database
        db.commit()
        db.refresh(user)
        
        # Return updated user info (excluding sensitive data)
        updated_user_info = {
            "theme": user.theme,
        }
        
        return UpdateUserInfoResponse(
            message="Theme updated successfully",
            user=updated_user_info
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Rollback any changes if an error occurred
        db.rollback()
        print(f"Error updating theme: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"An error occurred while updating theme: {str(e)}"
        )