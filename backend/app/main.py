import os
from fastapi import FastAPI, status, Header, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db import engine, get_async_session
from app.models import Base, User
from app.api.routes_comic import router as comic_router
from app.users import auth_backend, fastapi_users, UserManager
from app.schemas import UserRead, UserCreate, UserUpdate
from fastapi_users.db import SQLAlchemyUserDatabase

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Comic API",
    description="API for managing comics and their PDF files",
    version="1.0.0"
)

# CORS middleware
# Build allowed origins list
allowed_origins = [
    "http://localhost:3000",
    "http://localhost:5173",  # Vite default
    "https://comic-eight-dusky.vercel.app",
    "https://kuebiko-pr418eqvo-devansh-sharmas-projects-0a22b741.vercel.app",
]

# Add additional origins from environment variable (for preview deployments)
additional_origins = os.getenv("ADDITIONAL_CORS_ORIGINS", "")
if additional_origins:
    allowed_origins.extend([origin.strip() for origin in additional_origins.split(",")])

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global error handler for validation errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    body = exc.body
    try:
        # Try to serialize if possible, otherwise convert to string
        if not isinstance(body, (str, dict, list, int, float, bool, type(None))):
             body = str(body)
    except Exception:
        body = "Could not serialize body"

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors(), "body": body},
    )

# Include routers
app.include_router(comic_router)

# FastAPI Users Routers
app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"],
)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Comic API", "version": "1.0.0"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

# Admin Creation Endpoint
# Flag to prevent multiple admin creation
ADMIN_CREATED = False

class AdminCreateRequest(BaseModel):
    email: EmailStr
    password: str
    username: str = "admin"

@app.post("/create-admin")
async def create_admin_endpoint(
    admin: AdminCreateRequest,
    x_setup_token: str = Header(..., description="Setup token from environment"),
    session: AsyncSession = Depends(get_async_session)
):
    global ADMIN_CREATED
    
    # Verify setup token from environment variable
    setup_token = os.getenv("ADMIN_SETUP_TOKEN")
    if not setup_token:
        raise HTTPException(status_code=403, detail="Admin setup is disabled")
    
    if x_setup_token != setup_token:
        raise HTTPException(status_code=403, detail="Invalid setup token")
    
    # Check if any superuser already exists
    result = await session.execute(select(User).where(User.is_superuser))
    existing_admin = result.scalar_one_or_none()
    
    if existing_admin or ADMIN_CREATED:
        raise HTTPException(status_code=400, detail="Admin already exists")
    
    try:
        # Use fastapi-users UserManager to create admin
        user_db = SQLAlchemyUserDatabase(session, User)
        user_manager = UserManager(user_db)
        
        # Create user with superuser privileges
        user_create = UserCreate(
            email=admin.email,
            password=admin.password,
            is_superuser=True,
            is_verified=True
        )
        
        user = await user_manager.create(user_create)
        
        ADMIN_CREATED = True
        return {
            "message": "Admin created successfully",
            "user_id": user.id,
            "email": user.email,
            "warning": "Please remove ADMIN_SETUP_TOKEN from environment to disable this endpoint"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create admin: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
