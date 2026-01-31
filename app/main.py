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
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors(), "body": exc.body},
    )

# Include routers
app.include_router(comic_router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Comic API", "version": "1.0.0"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

