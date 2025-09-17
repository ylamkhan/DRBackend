from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
from app.models.models import User
from app.database import get_db
from sqlalchemy.orm import Session

# === Constants ===
SECRET_KEY = "8730fd2998ec298789a30ddb9f3e12b51182b0d6d85c4f63c905011452c313aa"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 30

# === Password Hashing ===
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

# === JWT Token Creation ===
def create_token(data: dict, expires_delta: timedelta, token_type: str):
    """
    Helper to create JWT tokens with a specified type.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire, "type": token_type}) # Add 'type' claim
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_access_token(data: dict):
    """Creates an access token with 'access' type."""
    return create_token(data, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES), "access")

def create_refresh_token(data: dict):
    """Creates a refresh token with 'refresh' type."""
    return create_token(data, timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS), "refresh")

# === JWT Token Decoding ===
def decode_jwt_token(token: str):
    """
    Decodes a JWT token and returns its payload.
    Returns None if the token is invalid (e.g., expired, malformed).
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

# === WebSocket Auth (Existing, unchanged, but noted here for completeness) ===
async def get_current_user_ws(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")  # This is the email you encoded in token
        if email is None:
            print("❌ Missing 'sub' in token.")
            return None

        db = next(get_db())
        user = db.query(User).filter(User.email == email).first()

        if user is None:
            print("❌ No user found with this email.")
        return user

    except JWTError as e:
        print(f"❌ JWT error: {e}")
        return None