# Comic API Backend

## Setup

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
# or
pip install -e .
```

### 2. PostgreSQL Setup

Make sure PostgreSQL is installed and running. Create a database:

```bash
createdb comics
```

### 3. Environment Variables

Create a `.env` file in the backend directory:

```bash
cp .env.example .env
```

Edit `.env` and update with your PostgreSQL credentials:

```
DATABASE_URL=postgresql://your_user:your_password@localhost:5432/comics
SECRET_KEY=your-secret-key
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
python main.py
# or
uvicorn app.main:app --reload
```

The API will be available at http://localhost:8000

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
