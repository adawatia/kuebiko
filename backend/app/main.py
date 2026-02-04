from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.db import engine
from app.models import Base
from app.api.routes_comic import router as comic_router

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Comic API",
    description="API for managing comics and their PDF files",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
# Include routers
app.include_router(comic_router)

# FastAPI Users Routers
from app.users import auth_backend, fastapi_users
from app.schemas import UserRead, UserCreate, UserUpdate

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

