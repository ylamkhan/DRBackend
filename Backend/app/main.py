from fastapi import FastAPI, WebSocket, status
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, dataset, data, quality,delete,upload,listfiles,deletefile,deleteaccout,theme,chat
from app.database import engine
from app.models import models
from app.api.websocket import quality_ws
from app.services.auth_utils import get_current_user_ws

from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

# ✅ Drop entire schema and recreate it (this removes all tables including users)
# with engine.connect() as conn:
#     conn.execute(text("DROP SCHEMA public CASCADE; CREATE SCHEMA public;"))
# print("❌ All tables dropped and schema recreated.")

# ✅ Let SQLAlchemy recreate tables (including users.created_at)
# models.Base.metadata.drop_all(bind=engine)
models.Base.metadata.create_all(bind=engine)
print("✅ All tables created.")

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- ADD THIS SECTION ---
# Define the base URL of your backend (important for constructing full image URLs)
BACKEND_BASE_URL = "http://127.0.0.1:8000"

# Mount the static files directory
# Assuming 'app' is the root of your Python package and 'static' is inside it
# So, if your main.py is in 'Backend/', and static files are in 'Backend/app/static/'
# the directory here should be 'app/static'
app.mount("/static", StaticFiles(directory="app/static"), name="static")
# ------------------------

# Routers
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(data.router, prefix="/data", tags=["data"])
app.include_router(dataset.router, prefix="/dataset", tags=["dataset"])
app.include_router(quality.router, prefix="/quality", tags=["quality"])
app.include_router(delete.router)
app.include_router(upload.router)
app.include_router(listfiles.router)
app.include_router(deletefile.router)
app.include_router(deleteaccout.router)
app.include_router(theme.router)
app.include_router(chat.router)

# WebSocket route
@app.websocket("/ws/quality")
async def websocket_quality(websocket: WebSocket):
    # Get token from query parameters
    token = websocket.query_params.get("token")
    if token is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # Validate token
    user = await get_current_user_ws(token)
    if user is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # Attach user if needed
    websocket.state.user = user

    # Accept connection only after validation
    await websocket.accept()

    # Delegate to quality handler
    await quality_ws(websocket)


# Create tables
# Base.metadata.create_all(bind=engine)
# app.include_router(dataset.router)
# app.include_router(upload.router)
# app.include_router(websocket.router)



