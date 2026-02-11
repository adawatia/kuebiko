# Comic API Backend

## Setup

### 1. Install Dependencies

We recommend using `uv` for package management, or `pip`.

```bash
cd backend
uv sync
# or
pip install -r requirements.txt
```

### 2. PostgreSQL Setup

Make sure PostgreSQL is installed and running. Create a database:

```bash
createdb kuebiko_db
```

### 3. Environment Variables

Create a `.env` file in the backend directory. Copy `.env.example` if available.

```bash
cp .env.example .env
```

Edit `.env` and update with your PostgreSQL credentials and ImageKit configuration.

```
DATABASE_URL=postgresql://your_user:your_password@localhost:5432/kuebiko_db
SECRET_KEY=your-secret-key-change-me
IMAGEKIT_PRIVATE_KEY=your_imagekit_private_key
IMAGEKIT_PUBLIC_KEY=your_imagekit_public_key
IMAGEKIT_URL_ENDPOINT=https://ik.imagekit.io/your_imagekit_id
```

### 4. Run Migrations

```bash
cd backend
alembic upgrade head
```

### 5. Create Superuser (Optional)

```bash
cd backend
python create_superuser.py
```

### 6. Run the Application

```bash
cd backend
uv run uvicorn main:app --reload
# or
python main.py
```

The API will be available at http://localhost:8000. 
For production, the backend is hosted on Render.

## Key Features

- **ImageKit Storage**: Comic covers and chapter images are stored on ImageKit.io for optimized delivery
- **Atomic Operations**: Helper logic ensures files and database records are kept in sync during uploads and failures
- **Bulk Operations**: Support for bulk deletion of comics and chapters
- **Authentication**: JWT-based auth with Superuser and User roles
- **Cloud Hosting**: Production deployment on Render with PostgreSQL database

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
