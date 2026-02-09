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

Edit `.env` and update with your PostgreSQL credentials. Note that file storage is now local (in `static/` directory) so no external storage keys are needed.

```
DATABASE_URL=postgresql://your_user:your_password@localhost:5432/kuebiko_db
SECRET_KEY=your-secret-key-change-me
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
Uploaded files will be served at `http://localhost:8000/static/`.

## Key Features

- **Local Storage**: Files (comic covers, PDFs) are stored locally in the `static/comics` directory.
- **Atomic Operations**: Helper logic ensures files and database records are kept in sync during uploads and failures.
- **Bulk Operations**: Support for bulk deletion of comics and chapters.
- **Authentication**: JWT-based auth with Superuser and User roles.

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
