from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
from enum import Enum
from sqlalchemy.dialects.postgresql import JSONB

Base = declarative_base()

class ComicStatus(str, Enum):
    ONGOING = "ongoing"
    COMPLETED = "completed"
    HIATUS = "hiatus"

class Comic(Base):
    __tablename__ = "comics"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(Text)
    cover_image_url = Column(String, nullable=True)
    author = Column(String)
    status = Column(String, default=ComicStatus.ONGOING.value) # Storing user's request as string enum
    genres = Column(JSONB) # Using JSONB as requested
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
    published_at = Column(DateTime(timezone=True), nullable=True)

    chapters = relationship("Chapter", back_populates="comic", cascade="all, delete-orphan", order_by="Chapter.chapter_number")

class Chapter(Base):
    __tablename__ = "chapters"
    id = Column(Integer, primary_key=True, index=True)
    comic_id = Column(Integer, ForeignKey("comics.id", ondelete="CASCADE"), nullable=False)
    chapter_number = Column(Float, nullable=False)
    title = Column(String)
    image_urls = Column(JSONB, default=list)  # Array of image URLs for the chapter
    page_count = Column(Integer, nullable=True)
    is_published = Column(Boolean, default=False)
    published_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    comic = relationship("Comic", back_populates="chapters")

    __table_args__ = (
        UniqueConstraint('comic_id', 'chapter_number', name='uix_comic_chapter'),
    )

from fastapi_users.db import SQLAlchemyBaseUserTable

class User(SQLAlchemyBaseUserTable[int], Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
