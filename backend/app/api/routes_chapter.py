from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from sqlalchemy.orm import Session
from app.db import SessionLocal
from app.models import Chapter, Comic, User
from app.schemas import ChapterCreate, ChapterUpdate, ChapterOut
from app.storage import storage_client
from app.users import current_active_user, current_superuser
from typing import List
from datetime import datetime

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
            pdf_url="", # Upload separately
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
    chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    return chapter

@router.get("/", response_model=List[ChapterOut])
def list_chapters(
    comic_id: int = Query(..., description="Filter by comic ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(current_active_user)
):
    """List chapters for a specific comic."""
    chapters = db.query(Chapter)\
        .filter(Chapter.comic_id == comic_id)\
        .order_by(Chapter.chapter_number)\
        .offset(skip)\
        .limit(limit)\
        .all()
    return chapters

@router.put("/{chapter_id}", response_model=ChapterOut)
def update_chapter(chapter_id: int, chapter_update: ChapterUpdate, db: Session = Depends(get_db), user: User = Depends(current_superuser)):
    chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    
    try:
        update_data = chapter_update.dict(exclude_unset=True)
        
        # Check duplicate chapter number if updated
        if "chapter_number" in update_data and update_data["chapter_number"] != chapter.chapter_number:
            if db.query(Chapter).filter(Chapter.comic_id == chapter.comic_id, Chapter.chapter_number == update_data["chapter_number"]).first():
                raise HTTPException(status_code=400, detail="Chapter number already exists for this comic.")

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

@router.post("/{chapter_id}/pdf", status_code=200)
async def upload_chapter_pdf(
    chapter_id: int,
    pdf: UploadFile = File(..., description="PDF file of the chapter."),
    db: Session = Depends(get_db),
    user: User = Depends(current_superuser)
):
    """Upload or replace the PDF file for a chapter."""
    chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    
    if not pdf.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")
    
    try:
        contents = await pdf.read()
        if len(contents) == 0:
            raise HTTPException(status_code=400, detail="Uploaded PDF is empty.")
        
        max_size = 100 * 1024 * 1024  # 100MB
        if len(contents) > max_size:
            raise HTTPException(status_code=400, detail="PDF file too large (max 100MB).")
        
        if not contents.lstrip().startswith(b'%PDF'):
            raise HTTPException(status_code=400, detail="File is not a valid PDF.")

        # Upload to storage
        filename = f"{chapter_id}_{pdf.filename}"
        
        # We need comic to get title if we want to follow existing pattern, but primary org is now ID-based.
        comic = db.query(Comic).filter(Comic.id == chapter.comic_id).first()
        if not comic:
            # Should not happen due to FK
            raise HTTPException(status_code=404, detail="Associated comic not found")

        old_pdf_url = chapter.pdf_url
        
        pdf_url = storage_client.upload_pdf(contents, comic.title, filename, comic_id=comic.id)
        
        chapter.pdf_url = pdf_url
        db.commit()
        db.refresh(chapter)
        
        if old_pdf_url:
            try:
                storage_client.delete_file(old_pdf_url)
            except:
                pass
                
        return {"ok": True, "pdf_url": pdf_url}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to upload PDF: {str(e)}")

@router.post("/batch-delete", status_code=status.HTTP_204_NO_CONTENT)
def bulk_delete_chapters(chapter_ids: List[int], db: Session = Depends(get_db), user: User = Depends(current_superuser)):
    """Delete multiple chapters and their associated PDF files."""
    try:
        chapters = db.query(Chapter).filter(Chapter.id.in_(chapter_ids)).all()
        if not chapters:
            return

        pdf_urls = [c.pdf_url for c in chapters if c.pdf_url]
        
        # Delete from DB
        db.query(Chapter).filter(Chapter.id.in_(chapter_ids)).delete(synchronize_session=False)
        db.commit()
        
        for pdf_url in pdf_urls:
            try:
                storage_client.delete_file(pdf_url)
            except Exception:
                pass

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to batch delete chapters: {str(e)}")

@router.delete("/{chapter_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_chapter(chapter_id: int, db: Session = Depends(get_db), user: User = Depends(current_superuser)):
    chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    
    pdf_url = chapter.pdf_url
    try:
        db.delete(chapter)
        db.commit()
        
        if pdf_url:
            try:
                storage_client.delete_file(pdf_url)
            except:
                pass
        return
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete chapter: {str(e)}")
