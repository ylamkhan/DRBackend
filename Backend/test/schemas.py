from pydantic import BaseModel, EmailStr

# Used for registration
class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str

# Used for login
class UserLogin(BaseModel):
    email: EmailStr
    password: str

# Return after register
class UserRead(BaseModel):
    id: int
    email: EmailStr
    full_name: str

    class Config:
        from_attributes = True


# Tokens returned after login
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class UserRead(BaseModel):
    id: int
    email: str
    full_name: str

    class Config:
        from_attributes = True
