from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional

class ComicGenre(str, Enum):
    ACTION = "Action"
    ADVENTURE = "Adventure"
    FANTASY = "Fantasy"
    HORROR = "Horror"
    ROMANCE = "Romance"
    SCIFI = "Sci-Fi"
    MYSTERY = "Mystery"
    OTHER = "Other"

from typing import List

class ComicBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)
    genres: List[ComicGenre]

class ComicCreate(ComicBase):
    """
    Comic creation schema.
    Example:
    {
        "title": "My Comic",
        "description": "A fun adventure.",
        "genres": ["Action", "Fantasy"]
    }
    """
    class Config:
        schema_extra = {
            "example": {
                "title": "My Comic",
                "description": "A fun adventure.",
                "genres": ["Action", "Fantasy"]
            }
        }

class ComicUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=1)
    genres: Optional[List[ComicGenre]] = None

class ComicOut(ComicBase):
    id: int
    pdf_path: str
    class Config:
        orm_mode = True
