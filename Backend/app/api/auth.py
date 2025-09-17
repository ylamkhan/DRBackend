from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer
# Import TokenRefreshRequest
from app.schemas.user import UserCreate, UserLogin, UserRead, Token, TokenRefreshRequest, ChangePassword
from app.models.models import User, UpdateUserInfoRequest, UpdateUserInfoResponse
from app.services import auth_utils
from app.database import get_db
from app.dependencies import get_current_user
from app.security.token_blacklist import blacklist_manager
from jose import JWTError # Import JWTError for token decoding errors

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

@router.post("/register", response_model=UserRead)
def register(user: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_pwd = auth_utils.hash_password(user.password)
    new_user = User(email=user.email, full_name=user.full_name, hashed_password=hashed_pwd)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return UserRead.from_orm(new_user)

@router.post("/login", response_model=Token)
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not auth_utils.verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token_data = {"sub": db_user.email}
    access_token = auth_utils.create_access_token(data=token_data)
    refresh_token = auth_utils.create_refresh_token(data=token_data)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.get("/me", response_model=UserRead)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.post("/logout")
def logout(current_user: User = Depends(get_current_user), token: str = Depends(oauth2_scheme)):
    """Get current user first to ensure token is valid, then blacklist it"""
    blacklist_manager.add_token(token)
    return {"detail": "Successfully logged out"}

# @router.post("/change-password")
# def change_password(
#     password_data: ChangePassword,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user),
# ):
#     # Check if current password is correct
#     if not auth_utils.verify_password(password_data.current_password, current_user.hashed_password):
#         raise HTTPException(status_code=401, detail="Current password is incorrect")

#     # Hash new password and update user
#     new_hashed_password = auth_utils.hash_password(password_data.new_password)
#     current_user.hashed_password = new_hashed_password
#     db.commit()
#     return {"detail": "Password changed successfully"}

# Optional: Change password endpoint
@router.post("/change-password")
async def change_password(
    password_data: dict,  # You can create a proper Pydantic model for this
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Changes the current user's password.
    Requires authentication and current password verification.
    """
    try:
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        current_password = password_data.get("current_password")
        new_password = password_data.get("new_password")
        
        if not current_password or not new_password:
            raise HTTPException(
                status_code=400, 
                detail="Both current password and new password are required"
            )
        
        if len(new_password) < 8:
            raise HTTPException(
                status_code=400, 
                detail="New password must be at least 8 characters long"
            )
        
        # Get the user from database
        user = db.query(User).filter(User.id == current_user.id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Verify current password
        if not pwd_context.verify(current_password, user.hashed_password):
            raise HTTPException(
                status_code=400, 
                detail="Current password is incorrect"
            )
        
        # Hash and update new password
        user.hashed_password = pwd_context.hash(new_password)
        
        # Update password change timestamp if you have one
        # user.password_changed_at = datetime.utcnow()
        
        db.commit()
        
        return {"message": "Password changed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Error changing password: {e}")
        raise HTTPException(
            status_code=500, 
            detail="An error occurred while changing the password"
        )

@router.post("/refresh-token", response_model=Token)
def refresh_token_endpoint(request_body: TokenRefreshRequest, db: Session = Depends(get_db)):
    """
    Refreshes an access token using a valid refresh token.
    Rotates the refresh token as well for enhanced security.
    """
    refresh_token_str = request_body.refresh_token

    # 1. Decode and validate the refresh token
    payload = auth_utils.decode_jwt_token(refresh_token_str)

    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    # 2. Check if the token is indeed a refresh token type
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Provided token is not a refresh token")

    email = payload.get("sub")
    if email is None:
        raise HTTPException(status_code=401, detail="Invalid refresh token payload: missing subject")

    db_user = db.query(User).filter(User.email == email).first()
    if db_user is None:
        raise HTTPException(status_code=401, detail="User not found for refresh token")

    # 3. Generate new access and refresh tokens (token rotation)
    new_access_token = auth_utils.create_access_token(data={"sub": db_user.email})
    new_refresh_token = auth_utils.create_refresh_token(data={"sub": db_user.email}) # Rotate refresh token

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }


@router.put("/update-user-info")
async def update_user_info(
    user_data: UpdateUserInfoRequest,
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
        
        # Check if email is already taken by another user
        if user_data.email != user.email:
            existing_user = db.query(User).filter(
                User.email == user_data.email,
                User.id != current_user.id
            ).first()
            if existing_user:
                raise HTTPException(
                    status_code=400, 
                    detail="Email address is already registered to another account"
                )
        
        # Update user information
        user.full_name = user_data.full_name
        user.email = user_data.email
        
        # Commit changes to database
        db.commit()
        db.refresh(user)
        
        # Return updated user info (excluding sensitive data)
        updated_user_info = {
            "id": user.id,
            "full_name": user.full_name,
            "email": user.email,
            "created_at": user.created_at.isoformat() if hasattr(user, 'created_at') else None,
            "updated_at": user.updated_at.isoformat() if hasattr(user, 'updated_at') else None
        }
        
        return UpdateUserInfoResponse(
            message="User information updated successfully",
            user=updated_user_info
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Rollback any changes if an error occurred
        db.rollback()
        print(f"Error updating user info: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"An error occurred while updating user information: {str(e)}"
        )