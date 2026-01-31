import os
import uuid
from typing import List
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, status
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError as FastAPIRequestValidationError
from sqlalchemy.orm import Session
from models import Comic, ComicGenre, Base
from schemas import ComicUpdate, ComicOut, ComicCreate
from database import engine, SessionLocal




UPLOAD_DIR = "uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)
Base.metadata.create_all(bind=engine)



app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Welcome to the Comic API"}

# Global error handler for validation errors
@app.exception_handler(FastAPIRequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors(), "body": exc.body},
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



# --- CRUD with JSON payloads ---
@app.post(
    "/comics/",
    response_model=ComicOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new comic",
    description="Create a new comic with metadata as JSON. Use /comics/{comic_id}/pdf to upload PDF after creation.",
)
def create_comic(
    comic: ComicCreate,
    db: Session = Depends(get_db)
):
    genre_objs = []
    for g in comic.genres:
        try:
            genre_objs.append(ComicGenre(g))
        except Exception:
            raise HTTPException(status_code=400, detail=f"Invalid genre: {g}")
    try:
        comic_db = Comic(
            title=comic.title,
            description=comic.description,
            genres=','.join([g.value for g in genre_objs]),
            pdf_path=None
        )
        db.add(comic_db)
        db.commit()
        db.refresh(comic_db)
        return ComicOut(
            id=comic_db.id,
            title=comic_db.title,
            description=comic_db.description,
            genres=genre_objs,
            pdf_path=comic_db.pdf_path
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create comic: {str(e)}")

@app.get("/comics/", response_model=List[ComicOut])
def list_comics(db: Session = Depends(get_db)):
    try:
        comics = db.query(Comic).all()
        result = []
        for comic in comics:
            genre_list = [ComicGenre(g) for g in comic.genres.split(',') if g]
            result.append(ComicOut(
                id=comic.id,
                title=comic.title,
                description=comic.description,
                genres=genre_list,
                pdf_path=comic.pdf_path
            ))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch comics: {str(e)}")

@app.get("/comics/{comic_id}", response_model=ComicOut)
def get_comic(comic_id: int, db: Session = Depends(get_db)):
    comic = db.query(Comic).filter(Comic.id == comic_id).first()
    if not comic:
        raise HTTPException(status_code=404, detail="Comic not found")
    genre_list = [ComicGenre(g) for g in comic.genres.split(',') if g]
    return ComicOut(
        id=comic.id,
        title=comic.title,
        description=comic.description,
        genres=genre_list,
        pdf_path=comic.pdf_path
    )

@app.get("/comics/{comic_id}/pdf")
def download_comic_pdf(comic_id: int, db: Session = Depends(get_db)):
    comic = db.query(Comic).filter(Comic.id == comic_id).first()
    if not comic:
        raise HTTPException(status_code=404, detail="Comic not found")
    if not comic.pdf_path or not os.path.exists(comic.pdf_path):
        raise HTTPException(status_code=404, detail="PDF not found")
    try:
        return FileResponse(comic.pdf_path, media_type="application/pdf", filename=os.path.basename(comic.pdf_path))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to download PDF: {str(e)}")

@app.put("/comics/{comic_id}", response_model=ComicOut)
def update_comic(comic_id: int, comic_update: ComicUpdate, db: Session = Depends(get_db)):
    comic = db.query(Comic).filter(Comic.id == comic_id).first()
    if not comic:
        raise HTTPException(status_code=404, detail="Comic not found")
    try:
        update_data = comic_update.dict(exclude_unset=True)
        if "genres" in update_data and update_data["genres"] is not None:
            genre_objs = []
            for g in update_data["genres"]:
                try:
                    genre_objs.append(ComicGenre(g))
                except Exception:
                    raise HTTPException(status_code=400, detail=f"Invalid genre: {g}")
            comic.genres = ','.join([g.value for g in genre_objs])
            update_data.pop("genres")
        for key, value in update_data.items():
            setattr(comic, key, value)
        db.commit()
        db.refresh(comic)
        genre_list = [ComicGenre(g) for g in comic.genres.split(',') if g]
        return ComicOut(
            id=comic.id,
            title=comic.title,
            description=comic.description,
            genres=genre_list,
            pdf_path=comic.pdf_path
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update comic: {str(e)}")
# --- PDF upload endpoint ---
@app.post("/comics/{comic_id}/pdf", status_code=200, summary="Upload PDF for a comic", description="Upload or replace the PDF file for a comic.")
async def upload_comic_pdf(
    comic_id: int,
    pdf: UploadFile = File(..., description="PDF file of the comic."),
    db: Session = Depends(get_db)
):
    comic = db.query(Comic).filter(Comic.id == comic_id).first()
    if not comic:
        raise HTTPException(status_code=404, detail="Comic not found")
    if not pdf.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")
    contents = await pdf.read()
    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="Uploaded PDF is empty.")
    max_size = 10 * 1024 * 1024  # 10MB
    if len(contents) > max_size:
        raise HTTPException(status_code=400, detail="PDF file too large (max 10MB).")
    if not contents.startswith(b'%PDF'):
        raise HTTPException(status_code=400, detail="File is not a valid PDF.")
    pdf_filename = f"{uuid.uuid4()}_{os.path.basename(pdf.filename)}"
    pdf_path = os.path.join(UPLOAD_DIR, pdf_filename)
    try:
        # Remove old PDF if exists
        if comic.pdf_path and os.path.exists(comic.pdf_path):
            os.remove(comic.pdf_path)
        with open(pdf_path, "wb") as buffer:
            buffer.write(contents)
        comic.pdf_path = pdf_path
        db.commit()
        db.refresh(comic)
        return {"ok": True, "pdf_path": pdf_path}
    except Exception as e:
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
        raise HTTPException(status_code=500, detail=f"Failed to upload PDF: {str(e)}")

@app.delete("/comics/{comic_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comic(comic_id: int, db: Session = Depends(get_db)):
    comic = db.query(Comic).filter(Comic.id == comic_id).first()
    if not comic:
        raise HTTPException(status_code=404, detail="Comic not found")
    try:
        if comic.pdf_path and os.path.exists(comic.pdf_path):
            try:
                os.remove(comic.pdf_path)
            except Exception:
                pass
        db.delete(comic)
        db.commit()
        return
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete comic: {str(e)}")
