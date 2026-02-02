from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.db import SessionLocal
from app.models import Comic, ComicGenre
from app.schemas import ComicCreate, ComicUpdate, ComicOut, ComicListResponse
from typing import List, Optional
import math
import uuid
import os

router = APIRouter(prefix="/comics", tags=["comics"])

UPLOAD_DIR = "uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

from app.users import current_active_user, current_superuser
from app.models import User

@router.post("/", response_model=ComicOut, status_code=status.HTTP_201_CREATED)
def create_comic(
    comic: ComicCreate,
    db: Session = Depends(get_db),
    user: User = Depends(current_superuser)
):
    """Create a new comic with JSON payload. Use POST /comics/{comic_id}/pdf to upload PDF separately."""
    
    # Check for duplicate title
    if db.query(Comic).filter(Comic.title == comic.title).first():
        raise HTTPException(status_code=400, detail="A comic with this title already exists.")

    try:
        comic_db = Comic(
            title=comic.title,
            description=comic.description,
            genres=','.join([g.value for g in comic.genres]),
            pdf_path=None
        )
        db.add(comic_db)
        db.commit()
        db.refresh(comic_db)
        db.commit()
        db.refresh(comic_db)
        try:
            genre_objs = [ComicGenre(g) for g in (comic_db.genres or "").split(',') if g]
        except ValueError:
            genre_objs = [] # Fallback for invalid genres in DB
        return ComicOut(
            id=comic_db.id,
            title=comic_db.title,
            description=comic_db.description,
            genres=genre_objs,
            pdf_path=comic_db.pdf_path or ""
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create comic: {str(e)}")

@router.get("/", response_model=ComicListResponse)
def list_comics(
    page: int = Query(1, ge=1, description="Page number"),
    items_per_page: int = Query(10, ge=1, le=100, alias="per_page", description="Items per page"),
    genres: Optional[List[str]] = Query(None, description="Filter by genres (OR logic)"),
    search: Optional[str] = Query(None, description="Search title or description"),
    db: Session = Depends(get_db),
    user: User = Depends(current_active_user)
):
    try:
        query = db.query(Comic)
        
        # Apply Search
        if search:
            search_query = f"%{search}%"
            query = query.filter(
                or_(
                    Comic.title.ilike(search_query),
                    Comic.description.ilike(search_query)
                )
            )
        
        # Apply Genres Filter (at least one genre must match)
        if genres:
            genre_filters = [Comic.genres.contains(g) for g in genres]
            query = query.filter(or_(*genre_filters))
            
        total_items = query.count()
        total_pages = math.ceil(total_items / items_per_page)
        
        offset = (page - 1) * items_per_page
        comics = query.offset(offset).limit(items_per_page).all()
        
        items = []
        for comic in comics:
            try:
                genre_list = [ComicGenre(g) for g in (comic.genres or "").split(',') if g]
            except ValueError:
                genre_list = []
            items.append(ComicOut(
                id=comic.id,
                title=comic.title,
                description=comic.description,
                genres=genre_list,
                pdf_path=comic.pdf_path
            ))
            
        return ComicListResponse(
            items=items,
            total_comics=total_items,
            total_pages=total_pages,
            current_page=page,
            items_per_page=items_per_page,
            next_page_available=page < total_pages,
            prev_page_available=page > 1
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch comics: {str(e)}")

@router.get("/{comic_id}", response_model=ComicOut)
def get_comic(comic_id: int, db: Session = Depends(get_db), user: User = Depends(current_active_user)):
    comic = db.query(Comic).filter(Comic.id == comic_id).first()
    if not comic:
        raise HTTPException(status_code=404, detail="Comic not found")
    try:
        genre_list = [ComicGenre(g) for g in (comic.genres or "").split(',') if g]
    except ValueError:
        genre_list = []
    return ComicOut(
        id=comic.id,
        title=comic.title,
        description=comic.description,
        genres=genre_list,
        pdf_path=comic.pdf_path
    )

@router.get("/{comic_id}/pdf")
def download_comic_pdf(comic_id: int, db: Session = Depends(get_db), user: User = Depends(current_active_user)):
    """Download the PDF file for a comic."""
    comic = db.query(Comic).filter(Comic.id == comic_id).first()
    if not comic:
        raise HTTPException(status_code=404, detail="Comic not found")
    if not comic.pdf_path or not os.path.exists(comic.pdf_path):
        raise HTTPException(status_code=404, detail="PDF not found")
    try:
        return FileResponse(
            comic.pdf_path, 
            media_type="application/pdf", 
            filename=os.path.basename(comic.pdf_path)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to download PDF: {str(e)}")

@router.put("/{comic_id}", response_model=ComicOut)
def update_comic(comic_id: int, comic_update: ComicUpdate, db: Session = Depends(get_db), user: User = Depends(current_superuser)):
    """Update comic metadata."""
    comic = db.query(Comic).filter(Comic.id == comic_id).first()
    if not comic:
        raise HTTPException(status_code=404, detail="Comic not found")
    try:
        update_data = comic_update.dict(exclude_unset=True)
        
        # Check duplicate title if title is being updated
        if "title" in update_data:
            existing_comic = db.query(Comic).filter(Comic.title == update_data["title"]).first()
            if existing_comic and existing_comic.id != comic_id:
                raise HTTPException(status_code=400, detail="A comic with this title already exists.")

        if "genres" in update_data:
            genres_data = update_data.pop("genres")
            if genres_data is not None:
                comic.genres = ','.join([g.value for g in genres_data])
            else:
                # Explicit null for genres? Let's ignore it or clear it. 
                # Here we assume it means 'no genres'.
                comic.genres = ""
                
        for key, value in update_data.items():
            setattr(comic, key, value)
        db.commit()
        db.refresh(comic)
        db.commit()
        db.refresh(comic)
        try:
            genre_list = [ComicGenre(g) for g in (comic.genres or "").split(',') if g]
        except ValueError:
            genre_list = []
        return ComicOut(
            id=comic.id,
            title=comic.title,
            description=comic.description,
            genres=genre_list,
            pdf_path=comic.pdf_path or ""
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update comic: {str(e)}")

@router.post("/{comic_id}/pdf", status_code=200)
async def upload_comic_pdf(
    comic_id: int,
    pdf: UploadFile = File(..., description="PDF file of the comic."),
    db: Session = Depends(get_db),
    user: User = Depends(current_superuser)
):
    """Upload or replace the PDF file for a comic."""
    comic = db.query(Comic).filter(Comic.id == comic_id).first()
    if not comic:
        raise HTTPException(status_code=404, detail="Comic not found")
    
    if not pdf.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")
    
    contents = await pdf.read()
    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="Uploaded PDF is empty.")
    
    max_size = 100 * 1024 * 1024  # 100MB
    if len(contents) > max_size:
        raise HTTPException(status_code=400, detail="PDF file too large (max 100MB).")
    
    if not contents.lstrip().startswith(b'%PDF'):
        raise HTTPException(status_code=400, detail="File is not a valid PDF.")
    
    pdf_filename = f"{uuid.uuid4()}_{os.path.basename(pdf.filename)}"
    pdf_path = os.path.join(UPLOAD_DIR, pdf_filename)
    
    old_pdf_path = comic.pdf_path
    try:
        # Write new PDF
        with open(pdf_path, "wb") as buffer:
            buffer.write(contents)
        
        # Update database
        comic.pdf_path = pdf_path
        db.commit()
        db.refresh(comic)
        
        # Remove old PDF if exists (after successful commit)
        if old_pdf_path and os.path.exists(old_pdf_path):
            try:
                os.remove(old_pdf_path)
            except Exception:
                pass  # Don't fail if old file can't be deleted
        
        return {"ok": True, "pdf_path": pdf_path}
    except Exception as e:
        # Cleanup new file if database update failed
        if os.path.exists(pdf_path):
            try:
                os.remove(pdf_path)
            except Exception:
                pass
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to upload PDF: {str(e)}")

@router.post("/batch-delete", status_code=status.HTTP_204_NO_CONTENT)
def bulk_delete_comics(comic_ids: List[int], db: Session = Depends(get_db), user: User = Depends(current_superuser)):
    """Delete multiple comics and their associated PDF files."""
    try:
        comics = db.query(Comic).filter(Comic.id.in_(comic_ids)).all()
        if not comics:
            return

        pdf_paths = [c.pdf_path for c in comics if c.pdf_path]
        
        # Delete from DB
        db.query(Comic).filter(Comic.id.in_(comic_ids)).delete(synchronize_session=False)
        db.commit()
        
        # Cleanup files
        for pdf_path in pdf_paths:
            if pdf_path and os.path.exists(pdf_path):
                try:
                    os.remove(pdf_path)
                except Exception:
                    pass
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to batch delete comics: {str(e)}")

@router.delete("/{comic_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comic(comic_id: int, db: Session = Depends(get_db), user: User = Depends(current_superuser)):
    """Delete a comic and its associated PDF file."""
    comic = db.query(Comic).filter(Comic.id == comic_id).first()
    if not comic:
        raise HTTPException(status_code=404, detail="Comic not found")
    
    pdf_path = comic.pdf_path
    try:
        db.delete(comic)
        db.commit()
        
        # Remove PDF file after successful database deletion
        if pdf_path and os.path.exists(pdf_path):
            try:
                os.remove(pdf_path)
            except Exception:
                pass  # Don't fail if file can't be deleted
        
        return
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete comic: {str(e)}")

