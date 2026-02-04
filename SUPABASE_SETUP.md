# Supabase Storage Integration Guide

This project now uses Supabase Storage for storing comic PDFs and cover images instead of local file storage.

## What Changed

### Backend Changes
- **Models**: Column names changed from `pdf_path` and `cover_image_path` to `pdf_url` and `cover_image_url`
- **Storage**: All file uploads now go directly to Supabase Storage
- **API**: Removed local file serving endpoints (`/comics/{id}/pdf` and `/comics/{id}/cover`)
- **Dependencies**: Added `supabase` Python package

### Frontend Changes
- **API Interface**: Updated `Comic` type to use `pdf_url` and `cover_image_url`
- **Display**: Images and PDFs are now loaded directly from Supabase URLs
- **PDF Reader**: Uses Supabase URLs directly instead of backend proxy

## Setup Instructions

### 1. Create Supabase Project

1. Go to [https://supabase.com](https://supabase.com) and create a new project
2. Wait for the project to be provisioned (takes ~2 minutes)

### 2. Create Storage Bucket

1. In your Supabase dashboard, go to **Storage**
2. Click **Create a new bucket**
3. Name it `comics` (or whatever you prefer)
4. Make it **Public** (so URLs can be accessed directly)
5. Click **Create bucket**

### 3. Set Up Bucket Policies (Optional)

For better security, you can configure RLS policies:

1. Go to **Storage** → **Policies**
2. Add policies for authenticated uploads and public reads
3. Example policy for public reads:
   ```sql
   CREATE POLICY "Public read access"
   ON storage.objects FOR SELECT
   USING (bucket_id = 'comics');
   ```

### 4. Configure Backend

1. Copy `.env.example` to `.env`:
   ```bash
   cp backend/.env.example backend/.env
   ```

2. Update the `.env` file with your Supabase credentials:
   ```env
   SUPABASE_URL=https://your-project-id.supabase.co
   SUPABASE_KEY=your-supabase-anon-key
   SUPABASE_BUCKET_NAME=comics
   ```

   You can find these values in your Supabase dashboard:
   - **URL**: Settings → API → Project URL
   - **Key**: Settings → API → Project API keys → `anon` `public` key (or `service_role` for admin operations)

3. Install the new dependency:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

### 5. Run Database Migration

Apply the migration to rename the database columns:

```bash
cd backend
alembic upgrade head
```

This will rename:
- `pdf_path` → `pdf_url`
- `cover_image_path` → `cover_image_url`

### 6. Migrate Existing Files (If Any)

If you have existing comics with local files, you'll need to migrate them to Supabase:

```python
# Example migration script (backend/migrate_to_supabase.py)
from app.db import SessionLocal
from app.models import Comic
from app.storage import supabase_storage
import os

db = SessionLocal()
comics = db.query(Comic).all()

for comic in comics:
    # Migrate PDF
    if comic.pdf_path and os.path.exists(comic.pdf_path):
        with open(comic.pdf_path, 'rb') as f:
            pdf_content = f.read()
            pdf_url = supabase_storage.upload_pdf(pdf_content, f"{comic.id}.pdf")
            comic.pdf_url = pdf_url
    
    # Migrate cover image
    if comic.cover_image_path and os.path.exists(comic.cover_image_path):
        with open(comic.cover_image_path, 'rb') as f:
            img_content = f.read()
            ext = os.path.splitext(comic.cover_image_path)[1]
            img_url = supabase_storage.upload_image(img_content, ext)
            comic.cover_image_url = img_url
    
    db.commit()
    print(f"Migrated comic: {comic.title}")

db.close()
```

### 7. Start the Application

```bash
# Backend
cd backend
uvicorn app.main:app --reload

# Frontend
cd frontend
npm run dev
```

## File Structure

```
backend/
├── app/
│   ├── storage.py          # NEW: Supabase storage utilities
│   ├── models.py           # UPDATED: url columns instead of path
│   ├── schemas.py          # UPDATED: url fields
│   └── api/
│       └── routes_comic.py # UPDATED: uses Supabase storage
└── alembic/
    └── versions/
        └── supabase_storage_urls.py  # NEW: migration

frontend/
└── src/
    ├── api/
    │   └── comics.ts       # UPDATED: url fields
    └── views/
        ├── HomeView.vue    # UPDATED: direct Supabase URLs
        └── ComicDetailView.vue  # UPDATED: direct Supabase URLs
```

## Benefits

1. **Scalability**: Supabase handles file storage and CDN
2. **Performance**: Direct file access without backend proxy
3. **Reliability**: Built-in redundancy and backups
4. **Cost**: No need for local storage infrastructure
5. **CDN**: Automatic global content delivery

## Troubleshooting

### Files not uploading
- Check your Supabase credentials in `.env`
- Verify the bucket exists and is public
- Check bucket size limits in Supabase dashboard

### Images not displaying
- Ensure bucket is set to **Public**
- Check browser console for CORS errors
- Verify URLs are correct in database

### Migration failed
- Ensure you have the latest code
- Check if columns already exist: `\d comics` in psql
- Try running: `alembic downgrade -1` then `alembic upgrade head`

## Security Notes

- The `anon` key is safe to use in frontend code
- For admin operations (delete), consider using `service_role` key in backend only
- Enable RLS policies for production use
- Set appropriate file size limits in Supabase dashboard
- Consider adding virus scanning for uploaded files

## Next Steps

- [ ] Add progress indicators for large file uploads
- [ ] Implement image optimization/resizing
- [ ] Add support for multiple cover images
- [ ] Implement CDN caching strategies
- [ ] Add file upload validation on Supabase side
