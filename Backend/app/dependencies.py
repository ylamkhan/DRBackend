# Enhanced dependencies.py with debugging
from fastapi import Depends, HTTPException, status
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from app.models.models import User
from app.database import get_db
from app.services.auth_utils import SECRET_KEY, ALGORITHM
from fastapi.security import OAuth2PasswordBearer
from app.security.token_blacklist import blacklist_manager

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    print("CHECKING TOKEN:", token)
    print("BLACKLIST SIZE:", blacklist_manager.get_blacklist_size())
    
    # Debug: Show first few characters of all blacklisted tokens
    with blacklist_manager._lock:
        for i, blacklisted_token in enumerate(blacklist_manager._blacklisted_tokens):
            print(f"BLACKLISTED TOKEN {i}: {blacklisted_token[:50]}...")
    
    # Debug: Check exact comparison
    is_blacklisted = blacklist_manager.is_blacklisted(token)
    print(f"IS BLACKLISTED: {is_blacklisted}")
    
    if is_blacklisted:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
        )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token payload")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    return user