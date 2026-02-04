from pydantic import BaseModel, Field, ConfigDict
from enum import Enum
from typing import Optional, List
from app.models import ComicGenre

class ComicBase(BaseModel):
    """Base comic schema with common fields"""
    title: str = Field(..., min_length=1, max_length=200, description="Comic title")
    description: str = Field(..., min_length=1, description="Comic description")
    genres: List[ComicGenre] = Field(..., min_length=1, description="List of genres")

class ComicCreate(ComicBase):
    """
    Schema for creating a new comic.
    
    Example:
    {
        "title": "My Amazing Comic",
        "description": "A thrilling adventure story",
        "genres": ["Action", "Fantasy"],
        "cover_image": "base64_encoded_string_here"
    }
    """
    cover_image: Optional[str] = Field(None, description="Base64 encoded cover image")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "My Amazing Comic",
                "description": "A thrilling adventure story",
                "genres": ["Action", "Fantasy"],
                "cover_image": "data:image/png;base64,..."
            }
        }
    )

class ComicUpdate(BaseModel):
    """Schema for updating an existing comic"""
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="Comic title")
    description: Optional[str] = Field(None, min_length=1, description="Comic description")
    genres: Optional[List[ComicGenre]] = Field(None, min_length=1, description="List of genres")
    cover_image: Optional[str] = Field(None, description="Base64 encoded cover image")

class ComicOut(ComicBase):
    """Schema for comic output"""
    id: int = Field(..., description="Comic ID")
    pdf_url: Optional[str] = Field(None, description="Supabase URL for PDF file")
    cover_image_url: Optional[str] = Field(None, description="Supabase URL for cover image")
    
    model_config = ConfigDict(from_attributes=True)

class ComicListResponse(BaseModel):
    """Paginated response for comic list"""
    items: List[ComicOut]
    total_comics: int = Field(..., description="Total number of comics available")
    total_pages: int = Field(..., description="Total number of pages")
    current_page: int = Field(..., description="Current page number")
    items_per_page: int = Field(..., description="Number of items per page")
    next_page_available: bool = Field(..., description="True if there is a next page")
    prev_page_available: bool = Field(..., description="True if there is a previous page")

from fastapi_users import schemas

class UserRead(schemas.BaseUser[int]):
    pass

class UserCreate(schemas.BaseUserCreate):
    pass

class UserUpdate(schemas.BaseUserUpdate):
    pass

