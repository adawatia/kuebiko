from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from sqlalchemy.orm import Session
from app.db import SessionLocal
from app.models import Chapter, Comic, User
from app.schemas import ChapterCreate, ChapterUpdate, ChapterOut, ChapterListResponse
from app.storage import storage_client
from app.users import current_active_user, current_superuser
from typing import List
from datetime import datetime
import math
import os

router = APIRouter(prefix="/chapters", tags=["chapters"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=ChapterOut, status_code=status.HTTP_201_CREATED)
def create_chapter(
    chapter: ChapterCreate,
    db: Session = Depends(get_db),
    user: User = Depends(current_superuser)
):
    """Create a new chapter."""
    comic = db.query(Comic).filter(Comic.id == chapter.comic_id).first()
    if not comic:
        raise HTTPException(status_code=404, detail="Comic not found")
        
    # Check for duplicate chapter number for this comic
    if db.query(Chapter).filter(Chapter.comic_id == chapter.comic_id, Chapter.chapter_number == chapter.chapter_number).first():
        raise HTTPException(status_code=400, detail="Chapter number already exists for this comic.")

    # Automatically set published_at if is_published is True
    published_at = chapter.published_at
    if chapter.is_published and not published_at:
        published_at = datetime.utcnow()

    try:
        chapter_db = Chapter(
            comic_id=chapter.comic_id,
            chapter_number=chapter.chapter_number,
            title=chapter.title,
            image_urls=[],  # Upload images separately
            page_count=chapter.page_count,
            is_published=chapter.is_published,
            published_at=published_at
        )
        db.add(chapter_db)
        db.commit()
        db.refresh(chapter_db)
        return chapter_db
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create chapter: {str(e)}")

@router.get("/{chapter_id}", response_model=ChapterOut)
def get_chapter(chapter_id: int, db: Session = Depends(get_db), user: User = Depends(current_active_user)):
    try:
        chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
        if not chapter:
            raise HTTPException(status_code=404, detail="Chapter not found")
        return chapter
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch chapter: {str(e)}")

@router.get("/", response_model=ChapterListResponse)
def list_chapters(
    comic_id: int = Query(..., description="Filter by comic ID"),
    page: int = Query(1, ge=1, description="Page number"),
    items_per_page: int = Query(10, ge=1, le=100, alias="per_page", description="Items per page"),
    db: Session = Depends(get_db),
    user: User = Depends(current_active_user)
):
    """List chapters for a specific comic with pagination."""
    try:
        query = db.query(Chapter).filter(Chapter.comic_id == comic_id).order_by(Chapter.chapter_number)
        
        total_items = query.count()
        total_pages = math.ceil(total_items / items_per_page) if total_items > 0 else 1
        
        offset = (page - 1) * items_per_page
        chapters = query.offset(offset).limit(items_per_page).all()
        
        return ChapterListResponse(
            items=chapters,
            total_chapters=total_items,
            total_pages=total_pages,
            current_page=page,
            items_per_page=items_per_page,
            next_page_available=page < total_pages,
            prev_page_available=page > 1
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch chapters: {str(e)}")

@router.put("/{chapter_id}", response_model=ChapterOut)
def update_chapter(chapter_id: int, chapter_update: ChapterUpdate, db: Session = Depends(get_db), user: User = Depends(current_superuser)):
    chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    
    try:
        update_data = chapter_update.model_dump(exclude_unset=True)
        
        # Check duplicate chapter number if updated
        if "chapter_number" in update_data and update_data["chapter_number"] != chapter.chapter_number:
            if db.query(Chapter).filter(Chapter.comic_id == chapter.comic_id, Chapter.chapter_number == update_data["chapter_number"]).first():
                raise HTTPException(status_code=400, detail="Chapter number already exists for this comic.")

        # Automatically set published_at if is_published becomes True
        if update_data.get("is_published") and not update_data.get("published_at") and not chapter.published_at:
            update_data["published_at"] = datetime.utcnow()

        for key, value in update_data.items():
            setattr(chapter, key, value)
            
        db.commit()
        db.refresh(chapter)
        return chapter
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update chapter: {str(e)}")


@router.post("/{chapter_id}/images", status_code=200)
async def upload_chapter_images(
    chapter_id: int,
    images: List[UploadFile] = File(..., description="Image files for the chapter pages."),
    db: Session = Depends(get_db),
    user: User = Depends(current_superuser)
):
    """Upload or replace the images for a chapter. Images are sorted by numeric filename."""
    chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    
    if not images:
        raise HTTPException(status_code=400, detail="No images provided")
    
    # Helper function to extract number from filename for sorting
    import re
    def extract_number(filename: str) -> int:
        """Extract the first number from filename for sorting."""
        match = re.search(r'(\d+)', filename)
        return int(match.group(1)) if match else 0
    
    # Sort images by numeric filename (e.g., 1.jpg, 2.jpg, 10.jpg, 20.jpg)
    # This ensures proper page order regardless of upload order
    sorted_images = sorted(images, key=lambda img: extract_number(img.filename or ""))
    
    # Validate all images first
    valid_extensions = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
    images_data = []
    extensions = []
    
    for img in sorted_images:
        if not img.filename:
            raise HTTPException(status_code=400, detail="Invalid image file")
        
        ext = os.path.splitext(img.filename.lower())[1]
        if ext not in valid_extensions:
            raise HTTPException(status_code=400, detail=f"Invalid file type: {img.filename}. Only JPG, PNG, GIF, and WebP are allowed.")
        
        contents = await img.read()
        if len(contents) == 0:
            raise HTTPException(status_code=400, detail=f"Uploaded image {img.filename} is empty.")
        
        max_size = 10 * 1024 * 1024  # 10MB per image
        if len(contents) > max_size:
            raise HTTPException(status_code=400, detail=f"Image {img.filename} is too large (max 10MB).")
        
        images_data.append(contents)
        extensions.append(ext)
    
    try:
        # Get comic for folder organization
        comic = db.query(Comic).filter(Comic.id == chapter.comic_id).first()
        if not comic:
            raise HTTPException(status_code=404, detail="Associated comic not found")

        # Store old image URLs for cleanup
        old_image_urls = chapter.image_urls or []
        
        # Upload new images (already sorted by filename number)
        image_urls = storage_client.upload_chapter_images(images_data, comic.id, chapter_id, extensions)
        
        # Update chapter with new image URLs and page count
        chapter.image_urls = image_urls
        chapter.page_count = len(image_urls)
        db.commit()
        db.refresh(chapter)
        
        # Cleanup old images
        for old_url in old_image_urls:
            try:
                storage_client.delete_file(old_url)
            except:
                pass
                
        return {"ok": True, "image_urls": image_urls, "page_count": len(image_urls)}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        # Cleanup uploaded files if DB update fails
        if 'image_urls' in locals() and image_urls:
            for url in image_urls:
                try:
                    storage_client.delete_file(url)
                except:
                    pass
        raise HTTPException(status_code=500, detail=f"Failed to upload images: {str(e)}")



@router.post("/batch-delete", status_code=status.HTTP_200_OK)
def batch_delete_chapters(chapter_ids: List[int], db: Session = Depends(get_db), user: User = Depends(current_superuser)):
    """Batch delete chapters and their associated images."""
    if not chapter_ids:
        raise HTTPException(status_code=400, detail="No chapter IDs provided")
    
    if len(chapter_ids) > 100:
        raise HTTPException(status_code=400, detail="Cannot delete more than 100 chapters at once")
    
    try:
        chapters = db.query(Chapter).filter(Chapter.id.in_(chapter_ids)).all()
        if not chapters:
            return {"message": "No chapters found to delete", "deleted_count": 0}

        # Collect all image URLs from all chapters
        all_image_urls = []
        for c in chapters:
            if c.image_urls:
                all_image_urls.extend(c.image_urls)
        
        deleted_count = len(chapters)
        
        # Delete from DB
        db.query(Chapter).filter(Chapter.id.in_(chapter_ids)).delete(synchronize_session=False)
        db.commit()
        
        # Delete all images
        for image_url in all_image_urls:
            try:
                storage_client.delete_file(image_url)
            except Exception:
                pass
                
        return {"message": f"Successfully deleted {deleted_count} chapter{'s' if deleted_count > 1 else ''}", "deleted_count": deleted_count}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to batch delete chapters: {str(e)}")

@router.delete("/{chapter_id}", status_code=status.HTTP_200_OK)
def delete_chapter(chapter_id: int, db: Session = Depends(get_db), user: User = Depends(current_superuser)):
    chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    
    image_urls = chapter.image_urls or []
    try:
        db.delete(chapter)
        db.commit()
        
        # Delete all chapter images
        for image_url in image_urls:
            try:
                storage_client.delete_file(image_url)
            except:
                pass
        return {"message": "Chapter deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete chapter: {str(e)}")
