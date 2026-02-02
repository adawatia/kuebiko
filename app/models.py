from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from enum import Enum

Base = declarative_base()

class ComicGenre(str, Enum):
    ACTION = "Action"
    ADVENTURE = "Adventure"
    FANTASY = "Fantasy"
    HORROR = "Horror"
    ROMANCE = "Romance"
    SCIFI = "Sci-Fi"
    MYSTERY = "Mystery"
    OTHER = "Other"

class Comic(Base):
    __tablename__ = "comics"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(Text)
    genres = Column(String, index=True)  # Comma-separated genres
    pdf_path = Column(String)
    cover_image_path = Column(String, nullable=True)

from fastapi_users.db import SQLAlchemyBaseUserTable

class User(SQLAlchemyBaseUserTable[int], Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
