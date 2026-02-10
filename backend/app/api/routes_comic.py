from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from app.db import SessionLocal
from app.models import Comic, ComicStatus
from app.schemas import ComicCreate, ComicUpdate, ComicOut, ComicListResponse, ComicOutPublic, ComicListResponsePublic
from app.storage import storage_client
from typing import List, Optional, Union
import math

router = APIRouter(prefix="/comics", tags=["comics"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

from app.users import current_active_user, current_superuser, fastapi_users
from app.models import User

@router.post("/", response_model=ComicOut, status_code=status.HTTP_201_CREATED)
def create_comic(
    comic: ComicCreate,
    db: Session = Depends(get_db),
    user: User = Depends(current_superuser)
):
    """Create a new comic."""
    
    # Check for duplicate title
    if db.query(Comic).filter(Comic.title == comic.title).first():
        raise HTTPException(status_code=400, detail="A comic with this title already exists.")

    try:
        comic_db = Comic(
            title=comic.title,
            description=comic.description,
            author=comic.author,
            status=comic.status.value,
            genres=comic.genres,
            cover_image_url=None
        )
        db.add(comic_db)
        db.commit()
        db.refresh(comic_db)

        cover_url = None
        if comic.cover_image:
            cover_url = storage_client.upload_base64_image(
                comic.cover_image,
                comic.title,
                comic_id=comic_db.id
            )
            comic_db.cover_image_url = cover_url
            db.commit()
            db.refresh(comic_db)
        
        return comic_db
    except HTTPException:
        # Re-raise HTTPException from storage layer
        db.rollback()
        if 'cover_url' in locals() and cover_url:
            try:
                storage_client.delete_file(cover_url)
            except:
                pass
        
        # If comic was created but image upload failed, remove it to avoid orphan rows
        try:
            if 'comic_db' in locals() and comic_db and comic_db.id:
                db.delete(comic_db)
                db.commit()
        except Exception:
            db.rollback()
            
        raise
    except Exception as e:
        # Cleanup image from storage if DB fails
        if 'cover_url' in locals() and cover_url:
            try:
                storage_client.delete_file(cover_url)
            except:
                pass
        db.rollback()
        # If comic was created, remove it to avoid orphan rows
        try:
            if 'comic_db' in locals() and comic_db and comic_db.id:
                db.delete(comic_db)
                db.commit()
        except Exception:
            db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create comic: {str(e)}")

@router.get("/", response_model=ComicListResponsePublic)
def list_comics(
    page: int = Query(1, ge=1, description="Page number"),
    items_per_page: int = Query(10, ge=1, le=100, alias="per_page", description="Items per page"),
    genres: Optional[List[str]] = Query(None, description="Filter by genres (OR logic)"),
    search: Optional[str] = Query(None, description="Search title or description"),
    db: Session = Depends(get_db)
):
    """List comics - returns public data without image URLs"""
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
            # For JSONB containing a list of strings, to check if it contains any of the input genres:
            # We can use OR condition with contains for each genre.
            # Comic.genres is a JSONB list.
            genre_filters = [Comic.genres.contains([g]) for g in genres]
            query = query.filter(or_(*genre_filters))
            
        total_items = query.count()
        total_pages = math.ceil(total_items / items_per_page)
        
        offset = (page - 1) * items_per_page
        comics = query.offset(offset).limit(items_per_page).all()
        
        items = []
        for comic in comics:
            # comic.genres is already a list from JSONB column
            genre_list = comic.genres if comic.genres else []
            
            items.append(ComicOutPublic(
                id=comic.id,
                title=comic.title,
                description=comic.description,
                author=comic.author,
                status=comic.status,
                genres=genre_list,
                cover_image_url=comic.cover_image_url,
                created_at=comic.created_at,
                updated_at=comic.updated_at,
                published_at=comic.published_at,
                chapters=[] # List view doesn't need chapters or expensive join
            ))
            
        return ComicListResponsePublic(
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

@router.get("/{comic_id}")
def get_comic(
    comic_id: int, 
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(fastapi_users.current_user(optional=True))
):
    """Get comic details - returns full data with image URLs if authenticated, public data otherwise"""
    try:
        comic = db.query(Comic).options(joinedload(Comic.chapters)).filter(Comic.id == comic_id).first()
        if not comic:
            raise HTTPException(status_code=404, detail="Comic not found")
        
        # Return full data if authenticated, public data otherwise
        if user:
            return ComicOut.model_validate(comic)
        else:
            return ComicOutPublic.model_validate(comic)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch comic: {str(e)}")

@router.put("/{comic_id}", response_model=ComicOut)
def update_comic(comic_id: int, comic_update: ComicUpdate, db: Session = Depends(get_db), user: User = Depends(current_superuser)):
    """Update comic metadata."""
    comic = db.query(Comic).filter(Comic.id == comic_id).first()
    if not comic:
        raise HTTPException(status_code=404, detail="Comic not found")
    try:
        update_data = comic_update.model_dump(exclude_unset=True)
        
        # Check duplicate title if title is being updated
        new_title = None
        if "title" in update_data:
            new_title = update_data["title"]
            existing_comic = db.query(Comic).filter(Comic.title == new_title).first()
            if existing_comic and existing_comic.id != comic_id:
                raise HTTPException(status_code=400, detail="A comic with this title already exists.")

        # Handle explicit genres list directly
        if "genres" in update_data:
            # It's already a list of strings or None
            # No special processing needed for JSONB if passed as list
            pass
                
        old_cover_url = None
        new_cover_url = None

        if "cover_image" in update_data:
            cover_image_b64 = update_data.pop("cover_image")
            if cover_image_b64:
                # Use new title if being updated, otherwise use current title
                title_for_storage = new_title if new_title else comic.title
                # Save new image to storage (stable folder by ID)
                new_cover_url = storage_client.upload_base64_image(
                    cover_image_b64,
                    title_for_storage,
                    comic_id=comic.id
                )
                
                # Mark old image for deletion (only if it's different)
                if comic.cover_image_url and comic.cover_image_url != new_cover_url:
                    old_cover_url = comic.cover_image_url
                
                comic.cover_image_url = new_cover_url
            elif cover_image_b64 is None: 
                # Remove cover
                old_cover_url = comic.cover_image_url
                comic.cover_image_url = None
                
        if "status" in update_data and update_data["status"]:
            update_data["status"] = update_data["status"].value

        for key, value in update_data.items():
            setattr(comic, key, value)
            
        db.commit()
        db.refresh(comic)
        
        # Cleanup old image from storage after successful commit
        if old_cover_url:
            try:
                storage_client.delete_file(old_cover_url)
            except:
                pass
                
        return comic
    except HTTPException:
        # Cleanup new file if it was created but operation failed
        if 'new_cover_url' in locals() and new_cover_url:
            try:
                storage_client.delete_file(new_cover_url)
            except:
                pass
        raise
    except Exception as e:
        # Cleanup new file if db rollback
        db.rollback()
        if 'new_cover_url' in locals() and new_cover_url:
            try:
                storage_client.delete_file(new_cover_url)
            except:
                pass
        raise HTTPException(status_code=500, detail=f"Failed to update comic: {str(e)}")

@router.post("/batch-delete", status_code=status.HTTP_200_OK)
def batch_delete_comics(comic_ids: List[int], db: Session = Depends(get_db), user: User = Depends(current_superuser)):
    """Batch delete comics by IDs."""
    if not comic_ids:
        raise HTTPException(status_code=400, detail="No comic IDs provided")
    
    if len(comic_ids) > 100:
        raise HTTPException(status_code=400, detail="Cannot delete more than 100 comics at once")
    
    try:
        comics = db.query(Comic).filter(Comic.id.in_(comic_ids)).all()
        if not comics:
            return {"message": "No comics found to delete", "deleted_count": 0}

        cover_urls = [c.cover_image_url for c in comics if c.cover_image_url]
        deleted_count = len(comics)
        deleted_ids = [c.id for c in comics]
        
        # Delete from DB
        db.query(Comic).filter(Comic.id.in_(comic_ids)).delete(synchronize_session=False)
        db.commit()
        
        for cover_url in cover_urls:
            try:
                storage_client.delete_file(cover_url)
            except Exception:
                pass

        # Cleanup folders to remove hierarchy
        for comic_id in deleted_ids:
            try:
                storage_client.delete_comic_folder(comic_id)
            except Exception:
                pass
                
        return {"message": f"Successfully deleted {deleted_count} comic{'s' if deleted_count > 1 else ''}", "deleted_count": deleted_count}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to batch delete comics: {str(e)}")

@router.delete("/{comic_id}", status_code=status.HTTP_200_OK)
def delete_comic(comic_id: int, db: Session = Depends(get_db), user: User = Depends(current_superuser)):
    """Delete a comic and its associated files from storage."""
    comic = db.query(Comic).filter(Comic.id == comic_id).first()
    if not comic:
        raise HTTPException(status_code=404, detail="Comic not found")
    
    cover_url = comic.cover_image_url
    try:
        db.delete(comic)
        db.commit()
        
        if cover_url:
            try:
                storage_client.delete_file(cover_url)
            except Exception:
                pass

        # Remove any remaining objects in the comic folder
        try:
            storage_client.delete_comic_folder(comic_id)
        except Exception:
            pass
        
        return {"message": "Comic and associated files deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete comic: {str(e)}")

