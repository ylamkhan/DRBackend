from typing import List, Optional
from pydantic import BaseModel, EmailStr, constr
from datetime import datetime

class UserChangePassword(BaseModel):
    old_password: str
    new_password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str



# IMPORTANT: Use the web-accessible URL path, not the file system path
DEFAULT_AVATAR_WEB_PATH = "/static/avatars/default.svg"

class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    avatar: Optional[str] = DEFAULT_AVATAR_WEB_PATH # Use the web path here
    theme: Optional[str] = 'dark'

class UserRead(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    avatar: Optional[str] = DEFAULT_AVATAR_WEB_PATH # Use the web path here
    theme: Optional[str] = 'dark'
    created_at: datetime

    class Config:
        from_attributes = True



class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class TokenRefreshRequest(BaseModel):
    refresh_token: str

class ChangePassword(BaseModel):
    current_password: constr(min_length=8)
    new_password: constr(min_length=8)



# app/schemas.py


class DatasetResponse(BaseModel):
    files: List[str]






