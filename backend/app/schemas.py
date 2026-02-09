from pydantic import BaseModel, Field, ConfigDict
from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.models import ComicStatus

class ChapterBase(BaseModel):
    chapter_number: float = Field(..., description="Chapter number (e.g. 1.0, 1.5)")
    title: str = Field(..., description="Chapter title")
    page_count: Optional[int] = Field(None, description="Number of pages")
    is_published: bool = Field(False, description="Is chapter published")
    published_at: Optional[datetime] = None

class ChapterCreate(ChapterBase):
    comic_id: int = Field(..., description="ID of the comic this chapter belongs to")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "comic_id": 1,
                "chapter_number": 1.0,
                "title": "The Beginning",
                "page_count": 20,
                "is_published": True
            }
        }
    )

class ChapterUpdate(BaseModel):
    chapter_number: Optional[float] = None
    title: Optional[str] = None
    page_count: Optional[int] = None
    is_published: Optional[bool] = None
    published_at: Optional[datetime] = None

class ChapterOut(ChapterBase):
    id: int
    comic_id: int
    pdf_url: Optional[str] = Field(None, description="PDF file URL")
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class ComicBase(BaseModel):
    """Base comic schema with common fields"""
    title: str = Field(..., min_length=1, max_length=200, description="Comic title")
    description: str = Field(..., min_length=1, description="Comic description")
    author: str = Field(..., min_length=1, description="Comic author")
    status: ComicStatus = Field(ComicStatus.ONGOING, description="Publication status")
    genres: List[str] = Field(..., description="List of genres")

class ComicCreate(ComicBase):
    """
    Schema for creating a new comic.
    """
    cover_image: Optional[str] = Field(None, description="Base64 encoded cover image") # For upload
    cover_image_url: Optional[str] = Field(None, description="URL") # direct url

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "My Amazing Comic",
                "description": "A thrilling adventure story",
                "author": "John Doe",
                "status": "ongoing",
                "genres": ["Action", "Fantasy"],
                "cover_image": "data:image/png;base64,..."
            }
        }
    )

class ComicUpdate(BaseModel):
    """Schema for updating an existing comic"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=1)
    author: Optional[str] = None
    status: Optional[ComicStatus] = None
    genres: Optional[List[str]] = None
    cover_image: Optional[str] = None
    cover_image_url: Optional[str] = None

class ComicOut(ComicBase):
    """Schema for comic output"""
    id: int = Field(..., description="Comic ID")
    cover_image_url: Optional[str] = Field(None, description="Storage URL for cover image")
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime] = None
    chapters: List[ChapterOut] = []
    
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

